"""Routers HTTP: solo transporte (parseo, delegación al servicio, serialización).

No hay try/except en esta capa: los servicios lanzan ``ApiError`` y el handler
global de ``app/main.py`` los convierte en la enveloppe JSON estándar.
"""
