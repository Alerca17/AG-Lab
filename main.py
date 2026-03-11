# =============================================================================
#  AG Lab — API Unificada
#  Problema 1: Mochila     → /mochila/*
#  Problema 2: Sensores    → /sensores/*
#  Archivos estáticos      → /  (carpeta static/)
#
#  Local:    uvicorn main:app --reload --port 8000
#  Railway:  se lanza automáticamente con el Procfile
# =============================================================================

from __future__ import annotations

import os
import random
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AG Lab API",
    description="Algoritmos Genéticos: Mochila + Sensores de Calidad del Aire",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
#  PROBLEMA 1 — MOCHILA
# =============================================================================

ITEMS = [
    {"id": 1, "kg": 12, "gain": 4},
    {"id": 2, "kg": 2,  "gain": 2},
    {"id": 3, "kg": 1,  "gain": 2},
    {"id": 4, "kg": 1,  "gain": 1},
    {"id": 5, "kg": 4,  "gain": 10},
]
CAPACITY = 15
N_GENES  = len(ITEMS)


class MochilaParams(BaseModel):
    pop_size: int   = Field(6,    ge=4,   le=100)
    p_sel:    float = Field(0.5,  ge=0.1, le=1.0)
    p_cross:  float = Field(0.86, ge=0.1, le=1.0)
    p_mut:    float = Field(0.7,  ge=0.0, le=1.0)
    max_iter: int   = Field(50,   ge=1,   le=1000)


class MochilaStepRequest(BaseModel):
    population: list[list[int]]
    generation: int
    best_ever:  Optional[list[int]] = None
    params:     MochilaParams


def m_random_chrom() -> list[int]:
    return [random.randint(0, 1) for _ in range(N_GENES)]

def m_fitness(c: list[int]) -> int:
    kg   = sum(c[i] * ITEMS[i]["kg"]   for i in range(N_GENES))
    gain = sum(c[i] * ITEMS[i]["gain"] for i in range(N_GENES))
    return gain if kg <= CAPACITY else 0

def m_weight(c: list[int]) -> int:
    return sum(c[i] * ITEMS[i]["kg"] for i in range(N_GENES))

def m_gain(c: list[int]) -> int:
    return sum(c[i] * ITEMS[i]["gain"] for i in range(N_GENES))

def m_display(c: list[int]) -> str:
    return "".join("5" if g else "7" for g in c)

def m_roulette(pop: list[list[int]], fits: list[int]) -> list[int]:
    total = sum(fits)
    if total == 0:
        return random.choice(pop)
    r, acc = random.uniform(0, total), 0
    for c, f in zip(pop, fits):
        acc += f
        if acc >= r:
            return c
    return pop[-1]

def m_crossover(a: list[int], b: list[int], p: float):
    if random.random() > p:
        return a[:], b[:]
    pt = random.randint(1, N_GENES - 1)
    return a[:pt] + b[pt:], b[:pt] + a[pt:]

def m_mutate(c: list[int], p: float) -> list[int]:
    return [1 - g if random.random() < p else g for g in c]

def m_build_ind(c: list[int], total: int) -> dict:
    f = m_fitness(c)
    w = m_weight(c)
    g = m_gain(c)
    return {
        "chromosome":      c,
        "display":         m_display(c),
        "fitness":         f,
        "weight":          w,
        "gain":            g,
        "valid":           w <= CAPACITY,
        "proportionality": round(f / total, 4) if total > 0 else 0.0,
        "items_included":  [ITEMS[i] for i, v in enumerate(c) if v == 1],
    }

def m_evolve(pop: list[list[int]], params: MochilaParams, best_ever) -> dict:
    fits     = [m_fitness(c) for c in pop]
    total    = sum(fits)
    avg      = total / len(pop)
    best_fit = max(fits)
    best_idx = fits.index(best_fit)
    if best_ever is None or best_fit > m_fitness(best_ever):
        best_ever = pop[best_idx][:]
    individuals = [m_build_ind(c, total) for c in pop]
    new_pop: list[list[int]] = []
    while len(new_pop) < len(pop):
        p1 = m_roulette(pop, fits)
        p2 = m_roulette(pop, fits)
        c1, c2 = m_crossover(p1, p2, params.p_cross)
        new_pop.append(m_mutate(c1, params.p_mut))
        if len(new_pop) < len(pop):
            new_pop.append(m_mutate(c2, params.p_mut))
    return {
        "individuals":    individuals,
        "total_fit":      total,
        "avg_fit":        round(avg, 4),
        "best_fit":       best_fit,
        "new_population": new_pop,
        "best_ever":      best_ever,
    }


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "2.0.0", "problems": ["mochila", "sensores"]}


@app.get("/mochila/items", tags=["Mochila"])
def mochila_items():
    return {"items": ITEMS, "capacity": CAPACITY, "n_genes": N_GENES}


@app.post("/mochila/run", tags=["Mochila"])
def mochila_run(params: MochilaParams):
    pop       = [m_random_chrom() for _ in range(params.pop_size)]
    best_ever = None
    generations, history = [], {"best": [], "avg": []}
    for gen in range(params.max_iter):
        r = m_evolve(pop, params, best_ever)
        generations.append({
            "generation": gen, "individuals": r["individuals"],
            "total_fit":  r["total_fit"], "avg_fit": r["avg_fit"], "best_fit": r["best_fit"],
        })
        history["best"].append(r["best_fit"])
        history["avg"].append(r["avg_fit"])
        pop, best_ever = r["new_population"], r["best_ever"]
    sol = best_ever
    return {
        "params": params.model_dump(), "total_gens": params.max_iter,
        "generations": generations, "fitness_history": history,
        "best_solution": {
            "chromosome":     sol,
            "display":        m_display(sol),
            "gain":           m_gain(sol),
            "weight":         m_weight(sol),
            "valid":          m_weight(sol) <= CAPACITY,
            "items_included": [ITEMS[i] for i, v in enumerate(sol) if v == 1],
        },
    }


@app.post("/mochila/step", tags=["Mochila"])
def mochila_step(req: MochilaStepRequest):
    pop = req.population or [m_random_chrom() for _ in range(req.params.pop_size)]
    if len(pop[0]) != N_GENES:
        raise HTTPException(400, f"Cromosoma debe tener {N_GENES} genes.")
    r    = m_evolve(pop, req.params, req.best_ever)
    done = req.generation + 1 >= req.params.max_iter
    sol  = r["best_ever"]
    return {
        "generation":     req.generation,
        "individuals":    r["individuals"],
        "total_fit":      r["total_fit"],
        "avg_fit":        r["avg_fit"],
        "best_fit":       r["best_fit"],
        "new_population": r["new_population"],
        "best_ever":      sol,
        "best_solution": {
            "chromosome":     sol,
            "display":        m_display(sol),
            "gain":           m_gain(sol),
            "weight":         m_weight(sol),
            "valid":          m_weight(sol) <= CAPACITY,
            "items_included": [ITEMS[i] for i, v in enumerate(sol) if v == 1],
        } if sol else None,
        "done": done,
    }


# =============================================================================
#  PROBLEMA 2 — SENSORES
# =============================================================================

UBICACIONES = [
    {"id": 1,  "nombre": "Centro Histórico",  "cobertura": 9,  "zona": "urbana",       "descripcion": "Alta densidad vehicular y peatonal"},
    {"id": 2,  "nombre": "Zona Industrial",   "cobertura": 10, "zona": "industrial",   "descripcion": "Fábricas y emisiones constantes"},
    {"id": 3,  "nombre": "Parque Central",    "cobertura": 5,  "zona": "verde",        "descripcion": "Zona de referencia limpia"},
    {"id": 4,  "nombre": "Autopista Norte",   "cobertura": 8,  "zona": "vial",         "descripcion": "Tráfico pesado y emisiones de CO2"},
    {"id": 5,  "nombre": "Barrio Residencial","cobertura": 4,  "zona": "residencial",  "descripcion": "Baja contaminación, valor de contraste"},
    {"id": 6,  "nombre": "Puerto/Aeropuerto", "cobertura": 9,  "zona": "logística",    "descripcion": "Keroseno y combustión de motores"},
    {"id": 7,  "nombre": "Universidad",       "cobertura": 6,  "zona": "educativa",    "descripcion": "Zona mixta con laboratorios"},
    {"id": 8,  "nombre": "Mercado Municipal", "cobertura": 7,  "zona": "comercial",    "descripcion": "Generadores y alta actividad humana"},
    {"id": 9,  "nombre": "Ribera del Río",    "cobertura": 6,  "zona": "natural",      "descripcion": "Contaminación hídrica y vapores"},
    {"id": 10, "nombre": "Estación de Trenes","cobertura": 8,  "zona": "transporte",   "descripcion": "Diésel y flujo masivo de personas"},
]
N_UBICACIONES = len(UBICACIONES)
SENSORES_META = 4
PEN_DEFAULT   = 20


class SensoresParams(BaseModel):
    pop_size:     int   = Field(8,    ge=4,   le=100)
    p_cross:      float = Field(0.86, ge=0.1, le=1.0)
    p_mut:        float = Field(0.1,  ge=0.0, le=1.0)
    max_iter:     int   = Field(100,  ge=1,   le=1000)
    penalizacion: int   = Field(20,   ge=1,   le=100)


class SensoresStepRequest(BaseModel):
    population: list[list[int]]
    generation: int
    best_ever:  Optional[list[int]] = None
    params:     SensoresParams


def s_random_chrom() -> list[int]:
    c = [0] * N_UBICACIONES
    for i in random.sample(range(N_UBICACIONES), SENSORES_META):
        c[i] = 1
    return c

def s_num(c: list[int]) -> int:
    return sum(c)

def s_cobertura(c: list[int]) -> int:
    return sum(c[i] * UBICACIONES[i]["cobertura"] for i in range(N_UBICACIONES))

def s_fitness(c: list[int], pen: int) -> int:
    return s_cobertura(c) - pen * abs(s_num(c) - SENSORES_META)

def s_roulette(pop: list[list[int]], fits: list[int]) -> list[int]:
    mn  = min(fits)
    adj = [f - mn + 1 for f in fits]
    tot = sum(adj)
    r, acc = random.uniform(0, tot), 0
    for c, a in zip(pop, adj):
        acc += a
        if acc >= r:
            return c
    return pop[-1]

def s_crossover(a: list[int], b: list[int], p: float):
    if random.random() > p:
        return a[:], b[:]
    pt = random.randint(1, N_UBICACIONES - 1)
    return a[:pt] + b[pt:], b[:pt] + a[pt:]

def s_mutate(c: list[int], p: float) -> list[int]:
    c = c[:]
    if random.random() < p:
        on  = [i for i, g in enumerate(c) if g == 1]
        off = [i for i, g in enumerate(c) if g == 0]
        if on and off:
            c[random.choice(on)]  = 0
            c[random.choice(off)] = 1
    return c

def s_build_ind(c: list[int], total: int, pen: int) -> dict:
    f     = s_fitness(c, pen)
    ns    = s_num(c)
    cob   = s_cobertura(c)
    delta = abs(ns - SENSORES_META)
    return {
        "chromosome":                c,
        "display":                   "".join(str(g) for g in c),
        "fitness":                   f,
        "num_sensores":              ns,
        "cobertura_bruta":           cob,
        "penalizacion_aplicada":     pen * delta,
        "valido":                    ns == SENSORES_META,
        "proporcionality":           round(f / total, 4) if total > 0 else 0.0,
        "ubicaciones_seleccionadas": [UBICACIONES[i] for i, v in enumerate(c) if v == 1],
    }

def s_build_solution(best: list[int], pen: int) -> dict:
    return {
        "chromosome":                best,
        "display":                   "".join(str(g) for g in best),
        "cobertura_total":           s_cobertura(best),
        "fitness":                   s_fitness(best, pen),
        "num_sensores":              s_num(best),
        "valido":                    s_num(best) == SENSORES_META,
        "ubicaciones_seleccionadas": [UBICACIONES[i] for i, v in enumerate(best) if v == 1],
    }

def s_evolve(pop: list[list[int]], params: SensoresParams, best_ever) -> dict:
    pen      = params.penalizacion
    fits     = [s_fitness(c, pen) for c in pop]
    total    = sum(f for f in fits if f > 0) or 1
    avg      = sum(fits) / len(pop)
    best_fit = max(fits)
    best_idx = fits.index(best_fit)
    if best_ever is None or best_fit > s_fitness(best_ever, pen):
        best_ever = pop[best_idx][:]
    individuals = [s_build_ind(c, total, pen) for c in pop]
    new_pop: list[list[int]] = []
    while len(new_pop) < len(pop):
        p1 = s_roulette(pop, fits)
        p2 = s_roulette(pop, fits)
        c1, c2 = s_crossover(p1, p2, params.p_cross)
        new_pop.append(s_mutate(c1, params.p_mut))
        if len(new_pop) < len(pop):
            new_pop.append(s_mutate(c2, params.p_mut))
    return {
        "individuals":    individuals,
        "total_fit":      total,
        "avg_fit":        round(avg, 4),
        "best_fit":       best_fit,
        "new_population": new_pop,
        "best_ever":      best_ever,
    }


@app.get("/sensores/ubicaciones", tags=["Sensores"])
def sensores_ubicaciones():
    return {
        "ubicaciones":   UBICACIONES,
        "n_ubicaciones": N_UBICACIONES,
        "sensores_meta": SENSORES_META,
        "penalizacion":  PEN_DEFAULT,
        "cobertura_maxima_posible": sum(
            sorted([u["cobertura"] for u in UBICACIONES], reverse=True)[:SENSORES_META]
        ),
    }


@app.post("/sensores/run", tags=["Sensores"])
def sensores_run(params: SensoresParams):
    pop       = [s_random_chrom() for _ in range(params.pop_size)]
    best_ever = None
    generations, history = [], {"best": [], "avg": []}
    for gen in range(params.max_iter):
        r = s_evolve(pop, params, best_ever)
        generations.append({
            "generation": gen, "individuals": r["individuals"],
            "total_fit":  r["total_fit"], "avg_fit": r["avg_fit"], "best_fit": r["best_fit"],
        })
        history["best"].append(r["best_fit"])
        history["avg"].append(r["avg_fit"])
        pop, best_ever = r["new_population"], r["best_ever"]
    return {
        "params": params.model_dump(), "total_gens": params.max_iter,
        "generations": generations, "fitness_history": history,
        "best_solution": s_build_solution(best_ever, params.penalizacion),
        "cobertura_maxima_posible": sum(
            sorted([u["cobertura"] for u in UBICACIONES], reverse=True)[:SENSORES_META]
        ),
    }


@app.post("/sensores/step", tags=["Sensores"])
def sensores_step(req: SensoresStepRequest):
    pop  = req.population or [s_random_chrom() for _ in range(req.params.pop_size)]
    r    = s_evolve(pop, req.params, req.best_ever)
    done = req.generation + 1 >= req.params.max_iter
    sol  = r["best_ever"]
    return {
        "generation":     req.generation,
        "individuals":    r["individuals"],
        "total_fit":      r["total_fit"],
        "avg_fit":        r["avg_fit"],
        "best_fit":       r["best_fit"],
        "new_population": r["new_population"],
        "best_ever":      sol,
        "best_solution":  s_build_solution(sol, req.params.penalizacion) if sol else None,
        "done":           done,
    }


# =============================================================================
#  STATIC FILES — siempre al final para no pisar las rutas de la API
# =============================================================================

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
