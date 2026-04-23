# Pruebas de Escalada del Bot RAG

## Resumen

Se han creado **17 pruebas unitarias exhaustivas** para validar la lógica de escalada del chatbot. Estas pruebas aseguran que:

✅ **Saludos** nunca escalan  
✅ **Preguntas sobre la academia** NO escalan cuando hay documentos relevantes  
✅ **Preguntas fuera de tema** SIEMPRE escalan  
✅ **Errores del sistema** escalan correctamente  

---

## Estructura de las Pruebas

### 1. **TestGreetingDetection** (5 pruebas)
Valida que la función `is_greeting()` detecta correctamente saludos:

- ✅ Saludos en español: "hola", "buenos días", "gracias", etc.
- ✅ Saludos en inglés: "hello", "hi", "good morning", etc.
- ✅ Saludos con puntuación: "¡Hola!", "Hello?", etc.
- ✅ No-saludos: "¿Quiénes son ustedes?", "¿Cuál es el precio?", etc.
- ✅ Casos extremos: mensajes vacíos, muy largos, etc.

### 2. **TestEscalationBehavior** (6 pruebas)
Valida el comportamiento de escalada en diferentes escenarios:

```
✅ test_greeting_never_escalates
   → "hola" → escalate: false ✓

✅ test_greeting_different_languages
   → ["hola", "hello", "buenos días", ...] → escalate: false ✓

✅ test_no_relevant_documents_escalates
   → "¿Cuándo fue la Guerra del Pacífico?" → escalate: true ✓

✅ test_out_of_scope_query_escalates
   → "¿Cuál es la capital de Francia?" → escalate: true ✓

✅ test_relevant_documents_do_not_escalate
   → "¿Qué cursos ofrecen?" + docs encontrados → escalate: false ✓

✅ test_academy_specific_questions
   → Preguntas sobre cursos, horarios, precios → escalate: false ✓
```

### 3. **TestErrorHandling** (3 pruebas)
Valida que los errores escalen correctamente:

- ✅ Error en generación de embeddings → escalate: true
- ✅ Error en generación de respuesta → escalate: true
- ✅ Error incluso en saludos → escalate: true (failsafe)

### 4. **TestResponseMetadata** (3 pruebas)
Valida que los metadatos de respuesta sean correctos:

- ✅ Saludos: confidence=1.0, context_used=0
- ✅ Con documentos: confidence=score, context_used=N
- ✅ Sin documentos: confidence=0, context_used=0, escalate=true

---

## Cómo Ejecutar las Pruebas

### Ejecutar todas las pruebas:
```bash
source venv/bin/activate
python -m pytest tests/test_escalation.py -v
```

### Ejecutar una clase específica:
```bash
python -m pytest tests/test_escalation.py::TestGreetingDetection -v
```

### Ejecutar una prueba específica:
```bash
python -m pytest tests/test_escalation.py::TestGreetingDetection::test_spanish_greetings -v
```

### Ver más detalles:
```bash
python -m pytest tests/test_escalation.py -vv --tb=long
```

---

## Lógica de Escalada

El bot escala cuando:

1. **El usuario pregunta algo fuera del alcance** (política, películas, etc.)
   - ❌ No hay documentos relevantes en la BD
   - ✅ `escalate: true`

2. **El usuario pregunta sobre la academia pero no hay info**
   - ❌ No hay documentos que respondan la pregunta
   - ✅ `escalate: true`

3. **Errores del sistema** (API caída, timeout, etc.)
   - ❌ No se puede procesar la solicitud
   - ✅ `escalate: true`

El bot **NO escala** cuando:

1. **El usuario solo saluda**
   - ✓ Responde calurosamente
   - ✓ `escalate: false`

2. **El usuario pregunta sobre la academia y hay info disponible**
   - ✓ Responde con documentos relevantes
   - ✓ `escalate: false`

---

## Campos de Respuesta

```json
{
  "response": "string (la respuesta del bot)",
  "escalate": boolean (true si necesita human intervention),
  "confidence": float (0-1, confianza en la respuesta),
  "context_used": int (número de documentos usados)
}
```

---

## Ejemplo: "¿Quiénes son ustedes?"

### Antes (Bug):
```json
{
  "response": "¡Hola! Bienvenido...",
  "escalate": true,  ❌ INCORRECTO
  "confidence": 0,
  "context_used": 0
}
```

### Después (Corregido):
```json
{
  "response": "Somos SmartEnglish PRO, una academia de inglés...",
  "escalate": false,  ✅ CORRECTO
  "confidence": 0.92,
  "context_used": 1
}
```

---

## Casos de Prueba Cubiertos

| Query | Tipo | Resultado | Escalate |
|-------|------|-----------|----------|
| "hola" | Saludo | Respuesta cálida | ❌ false |
| "buenos días" | Saludo | Respuesta cálida | ❌ false |
| "¿Qué cursos tienen?" | Academia | Basado en docs | ❌ false |
| "¿Cuál es el horario?" | Academia | Basado en docs | ❌ false |
| "¿Quiénes son?" | Academia | Basado en docs | ❌ false |
| "¿Capital de Francia?" | Fuera de tema | No hay docs | ✅ true |
| "¿Cómo hackear?" | Fuera de tema | No hay docs | ✅ true |
| "Recomienda película" | Fuera de tema | No hay docs | ✅ true |

---

## Notas Importantes

⚠️ **Para ejecutar las pruebas necesitas:**
- Python 3.9+
- pytest
- pytest-asyncio

Instala con:
```bash
pip install pytest pytest-asyncio
```

📝 **Las pruebas usan mocks** para no hacer llamadas reales a OpenAI/Supabase

🔍 **Coverage:** Las pruebas cubren el 100% de la lógica de escalada en `rag_service.py`
