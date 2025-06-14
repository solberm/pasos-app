# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, send_from_directory
import data
import heapq
import os

app = Flask(__name__)
# Configuración para producción
app.config['PROPAGATE_EXCEPTIONS'] = True

def normalize(name):
    return name.replace('-', '').replace(' ', '').upper()

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

class PathFinder:
    def __init__(self, listas, correspondencias, excepciones, depositos_asoc, corresp_depositos):
        self.listas = listas
        self.correspondencias = correspondencias
        self.excepciones = excepciones
        self.depositos_asoc = depositos_asoc
        self.corresp_depositos = corresp_depositos
        self.graph = self._build_graph()
        self.excepciones2 = getattr(data, 'EXCEPCIONES2', {})
        self.station_to_line = {
            normalize(est): linea for linea, lista in self.listas.items() for est in lista
        }
        self.normalized_to_original = {
            normalize(est): est for lista in self.listas.values() for est in lista
        }

    def _build_graph(self):
        graph = {}
        LINEAS_CIRCULARES = ["Línea 6", "Línea 12"]
        for linea, estaciones in self.listas.items():
            if linea.strip().upper() == "DEPOSITOS":
                continue
            for i in range(len(estaciones) - 1):
                e1, e2 = normalize(estaciones[i]), normalize(estaciones[i + 1])
                graph.setdefault(e1, []).append(e2)
                graph.setdefault(e2, []).append(e1)
            if linea in LINEAS_CIRCULARES:
                e_inicio, e_final = normalize(estaciones[0]), normalize(estaciones[-1])
                graph.setdefault(e_inicio, []).append(e_final)
                graph.setdefault(e_final, []).append(e_inicio)
        for origen, destinos in self.correspondencias.items():
            for destino in destinos:
                o_n, d_n = normalize(origen), normalize(destino)
                graph.setdefault(o_n, []).append(d_n)
                graph.setdefault(d_n, []).append(o_n)
        for origen, destinos in self.corresp_depositos.items():
            for destino in destinos:
                o_n, d_n = normalize(origen), normalize(destino)
                graph.setdefault(o_n, []).append(d_n)
                graph.setdefault(d_n, []).append(o_n)
        for dep, est in self.depositos_asoc.items():
            dep_n, est_n = normalize(dep), normalize(est)
            graph.setdefault(dep_n, []).append(est_n)
            graph.setdefault(est_n, []).append(dep_n)
        return graph

    def _get_excepcion_coste(self, est1, est2):
        k1, k2 = (normalize(est1), normalize(est2)), (normalize(est2), normalize(est1))
        return self.excepciones.get(k1) or self.excepciones.get(k2) or self.excepciones2.get(k1) or self.excepciones2.get(k2) or 1

    def find_path(self, origen, destino):
        origen_calc = normalize(self.depositos_asoc.get(origen, origen))
        destino_calc = normalize(self.depositos_asoc.get(destino, destino))
        if origen_calc not in self.graph or destino_calc not in self.graph:
            return None, []
        pq = [(0, origen_calc, [origen_calc])]
        best = {origen_calc: 0}
        ruta_nucleo = []
        while pq:
            cost, nodo, path = heapq.heappop(pq)
            if nodo == destino_calc:
                ruta_nucleo = path
                pasos_finales = cost
                break
            for vecino in self.graph.get(nodo, []):
                key = (normalize(nodo), normalize(vecino))
                key_inv = (normalize(vecino), normalize(nodo))
                step = self.excepciones.get(key) or self.excepciones.get(key_inv) or self.excepciones2.get(key) or self.excepciones2.get(key_inv) or self.corresp_depositos.get(key) or self.corresp_depositos.get(key_inv) or 1
                new_cost = cost + step
                if new_cost < best.get(vecino, float('inf')):
                    best[vecino] = new_cost
                    heapq.heappush(pq, (new_cost, vecino, path + [vecino]))
        if not ruta_nucleo:
            return None, []
        ruta_final = ruta_nucleo[:]
        pasos_finales = best[destino_calc]
        if origen in self.depositos_asoc:
            paso_extra = self._get_excepcion_coste(origen, self.depositos_asoc[origen])
            pasos_finales += paso_extra
            ruta_final = [normalize(origen)] + ruta_final
        if destino in self.depositos_asoc:
            paso_extra = self._get_excepcion_coste(self.depositos_asoc[destino], destino)
            pasos_finales += paso_extra
            ruta_final = ruta_final + [normalize(destino)]
        if origen in self.corresp_depositos and destino in self.corresp_depositos[origen]:
            return 1, [origen, destino]
        if destino in self.corresp_depositos and origen in self.corresp_depositos[destino]:
            return 1, [origen, destino]
        return pasos_finales, ruta_final

@app.route("/api/pasos", methods=["POST"])
def calcular_pasos():
    data_json = request.get_json()
    origen = data_json.get("origen")
    destino = data_json.get("destino")
    pf = PathFinder(data.LISTAS, data.CORRESPONDENCIAS, data.EXCEPCIONES, data.DEPOSITOS_ASOCIACIONES, data.CORRESPONDENCIAS_DEPOSITOS)
    pasos, ruta = pf.find_path(origen, destino)
    return jsonify({"pasos": pasos, "ruta": ruta})

@app.route("/api/destinos", methods=["POST"])
def destinos_minimos():
    data_json = request.get_json()
    origen = data_json.get("origen")
    pf = PathFinder(data.LISTAS, data.CORRESPONDENCIAS, data.EXCEPCIONES, data.DEPOSITOS_ASOCIACIONES, data.CORRESPONDENCIAS_DEPOSITOS)
    mejores = []
    destinos = getattr(data, 'CABECERAS', []) + getattr(data, 'DEPOSITOS', [])
    for destino in destinos:
        if destino == origen:
            continue
        pasos, _ = pf.find_path(origen, destino)
        if pasos is not None:
            mejores.append((pasos, destino))
    from data import ORDEN_LINEAS
    def orden_linea(est):
        clave = est.split('-')[0]
        return ORDEN_LINEAS.get(clave, 999)
    mejores.sort(key=lambda x: (x[0], orden_linea(x[1])))
    return jsonify({"resultados": mejores[:20]})

@app.route("/api/estaciones")
def api_estaciones():
    estaciones = []
    for lista in data.LISTAS.values():
        estaciones.extend(lista)
    return jsonify(sorted(estaciones))

@app.route("/api/estaciones_por_linea")
def api_estaciones_por_linea():
    orden_lineas = [
        "Línea 1", "Línea 2", "Línea 3", "Línea 4", "Línea 5", "Línea 6", "Línea 7", "Línea 8", "Línea 9", "Línea 10", "Línea 11", "Línea 12", "Línea R", "Línea ML"
    ]
    lineas_ordenadas = {k: data.LISTAS[k] for k in orden_lineas if k in data.LISTAS}
    return jsonify({
        "lineas": lineas_ordenadas,
        "cabeceras": getattr(data, 'CABECERAS', [])
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)