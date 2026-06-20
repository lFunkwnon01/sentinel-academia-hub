# Checklist de Entrega Final - Criterio 5

> Marca cada item conforme lo completes.
> Este es el ultimo paso antes de entregar la hackaton.

---

## Indice
1. [Codigo y Calidad](#1-codigo-y-calidad)
2. [Documentacion](#2-documentacion)
3. [Demo y Evidencias](#3-demo-y-evidencias)
4. [Deploy](#4-deploy)
5. [Seguridad](#5-seguridad)
6. [Verificacion Final](#6-verificacion-final)

---

## 1. Codigo y Calidad

### Backend
- [ ] `npm run typecheck` pasa sin errores
- [ ] `npm run lint` pasa sin warnings
- [ ] `npm run test` todos los tests pasan
- [ ] `npm run build` exitoso
- [ ] Cero `any` en TypeScript
- [ ] Cero `@ts-ignore` / `@ts-expect-error`
- [ ] Cero `console.log` (solo `logger`)
- [ ] Cero secrets hardcodeados
- [ ] Validacion Zod en TODA Lambda
- [ ] Correlation ID en TODA respuesta
- [ ] Cada Lambda = 1 endpoint
- [ ] SAM template valida (`sam validate`)

### Frontend
- [ ] `cd web && npm run typecheck` pasa sin errores
- [ ] `cd web && npm run lint` pasa sin warnings
- [ ] `cd web && npm run test` todos pasan
- [ ] `cd web && npm run build` exitoso
- [ ] Cero errores en consola del navegador
- [ ] Lighthouse Performance > 80
- [ ] Lighthouse Accessibility > 90
- [ ] Sin errores en consola al navegar todas las vistas
- [ ] Mobile responsive (probar en DevTools)

### Git
- [ ] Branch `main` con codigo de produccion
- [ ] Commits en espanol con Conventional Commits
- [ ] No commits con "WIP" sueltos
- [ ] .gitignore actualizado
- [ ] Sin node_modules, .env, dist committeados
- [ ] Git history limpio (commits pequenos)

---

## 2. Documentacion

### README raiz
- [ ] Badges (CI, license, etc.)
- [ ] Descripcion del proyecto (1 parrafo)
- [ ] Demo / GIF / video embebido
- [ ] Arquitectura (imagen + link a docs)
- [ ] Quick start (3 comandos)
- [ ] Stack tecnologico
- [ ] Links a documentacion de cada criterio

### Documentacion por criterio
- [x] **C1**: `docs/01-contexto/contexto.pdf` (compilado)
- [x] **C2**: `docs/02-arquitectura/arquitectura.md` + 4 diagramas PNG/SVG
- [x] **C3**: `docs/03-resiliencia-llm/resiliencia.pdf` + checklist.md
- [x] **C4**: `docs/04-frontend/` (arquitectura, componentes, mock-flow)
- [x] **C5**: `docs/05-repo-deploy/` (checklist, manual-deploy, costos)

### Adicionales
- [x] LICENSE (MIT)
- [x] CHANGELOG.md
- [x] .github/workflows/ci.yml

---

## 3. Demo y Evidencias

### Video demo (obligatorio)
- [ ] Grabar video de 2-3 minutos mostrando:
  - [ ] Form de queja funcional
  - [ ] Confirmacion de envio
  - [ ] Dashboard con metricas
  - [ ] Chat con respuesta del LLM
- [ ] Subir video a YouTube (unlisted) o Loom
- [ ] Pegar link en el README

### Screenshots
- [ ] Screenshot del Home
- [ ] Screenshot del Form de queja
- [ ] Screenshot del Dashboard
- [ ] Screenshot del Chat
- [ ] Screenshot del flujo en CloudWatch (si deployaste)

### GIF
- [ ] GIF corto del flujo end-to-end (opcional pero recomendado)

---

## 4. Deploy

### Backend (AWS Academy)
- [ ] `sam build` exitoso
- [ ] `sam deploy --guided` primera vez (guardar samconfig.toml)
- [ ] Outputs del stack guardados
- [ ] Smoke test: POST /api/quejas responde 202
- [ ] Lambda processQueja se invoca correctamente
- [ ] DynamoDB tiene items
- [ ] SNS publica cuando criticidad=CRITICA
- [ ] CloudWatch Logs sin errores

### OCI (LLM)
- [ ] `oci-cli` instalado y configurado
- [ ] Compartment creado
- [ ] Test de OCI GenAI con prompt de ejemplo exitoso
- [ ] Secrets en OCI Vault

### Frontend (Vercel)
- [ ] Cuenta en Vercel
- [ ] Repo conectado
- [ ] VITE_API_URL configurado
- [ ] Deploy en produccion exitoso
- [ ] URL publica accesible
- [ ] Form de queja funcional desde URL publica
- [ ] Sin errores en consola

### CI/CD
- [ ] GitHub Actions configurado
- [ ] Secrets de AWS Academy en GitHub Secrets
- [ ] Workflow pasa en cada push
- [ ] Deploy automatico a Vercel configurado

---

## 5. Seguridad

- [ ] `git secrets` configurado (prevenir commit de secrets)
- [ ] `.env.example` sin valores reales
- [ ] AWS IAM con minimo privilegio
- [ ] API Gateway con rate limiting
- [ ] CORS configurado correctamente
- [ ] Validacion Zod en TODA entrada
- [ ] Correlation ID en respuestas
- [ ] Anonimizacion en el output del LLM
- [ ] Sin secrets en logs
- [ ] HTTPS everywhere (Vercel + API Gateway)

---

## 6. Verificacion Final

### Funcional
- [ ] Puedo crear una queja desde el frontend
- [ ] La queja aparece en el dashboard en < 30s
- [ ] Si la queja es CRITICA, llega notificacion
- [ ] El chat responde con informacion relevante
- [ ] El dashboard muestra metricas correctas
- [ ] Las paginas son navegables y no rompen

### Documental
- [ ] Puedo explicar el problema sin leer el PDF
- [ ] Puedo dibujar la arquitectura de memoria
- [ ] Puedo explicar cada patron de resiliencia
- [ ] Puedo demostrar el frontend funcionando
- [ ] Tengo el video demo listo

### Tecnico
- [ ] `npm run typecheck` clean
- [ ] `npm run lint` clean
- [ ] `npm run docs:all` compila sin errores
- [ ] `npm run openapi:lint` pasa
- [ ] Mock funciona localmente
- [ ] Deploy funciona

### Costo
- [ ] Verificado que AWS Academy credits < $5 gastados
- [ ] Verificado que OCI credits < $5 gastados
- [ ] Vercel sigue en free tier
- [ ] Budget alert configurado

---

## Resumen de Entregables

### Codigo
- [x] Config opencode (5 agents, 7 rules, 16 skills, 4 MCPs)
- [ ] Backend: 9 Lambdas funcionales
- [ ] Frontend: Vue 3 con 5 vistas
- [ ] OpenAPI spec con 7 endpoints
- [ ] SAM template (IaC)
- [ ] GitHub Actions CI

### Documentacion
- [x] Contexto LaTeX → PDF
- [x] 4 diagramas de arquitectura (Mermaid + PNG/SVG)
- [x] Resiliencia LaTeX → PDF (16+ paginas)
- [x] Checklist de 100+ items
- [x] Documentacion frontend (3 archivos)
- [x] Manual de deploy
- [x] Estimacion de costos
- [x] README completo
- [x] LICENSE + CHANGELOG

### Demo
- [ ] Frontend desplegado en Vercel (URL publica)
- [ ] Backend desplegado en AWS (URL de API Gateway)
- [ ] Video demo de 2-3 min
- [ ] Screenshots / GIF

---

## Rubrica esperada

| Criterio | Puntos esperados | Justificacion |
|---|---|---|
| 1. Contexto | **4/4** | PDF completo con problema, personas, impacto, viabilidad |
| 2. Arquitectura | **4/4** | 4 diagramas C4 + multi-nube + justificaciones + costos |
| 3. Resiliencia + LLM | **4/4** | 9 estrategias implementadas + checklist + diagrama de flujo |
| 4. Frontend | **4/4** | Vue 3 deployed, form, dashboard, chat, responsive, accesible |
| 5. Repo + Deploy | **4/4** | README, CI, IaC, deploy automatizado, video demo |
| **TOTAL** | **20/20** | |

---

## Troubleshooting rapido

### "npm run typecheck falla"

```bash
# Backend
cd src && npx tsc --noEmit

# Frontend
cd web && npx vue-tsc --noEmit
```

### "Mock no responde"

```bash
# Verificar que el puerto 4010 esta libre
lsof -i :4010

# Verificar que el spec es valido
npx @redocly/cli lint api-mock/openapi.yaml
```

### "Tectonic no compila"

```bash
# Verificar instalacion
which tectonic || ~/.local/bin/tectonic --version

# Si no esta, instalar
curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.16.9/tectonic-0.16.9-x86_64-unknown-linux-musl.tar.gz" -o /tmp/tectonic.tar.gz
tar -xzf /tmp/tectonic.tar.gz -C /tmp
mv /tmp/tectonic ~/.local/bin/
```

### "Deploy a AWS falla"

```bash
# Verificar credenciales de Academy
aws sts get-caller-identity

# Verificar LabRole existe
aws iam get-role --role-name LabRole

# Limpiar cache
rm -rf .aws-sam/
sam build --use-container
```

---

## Cuando termines

1. Commit final con todos los cambios
2. Push a `main`
3. Verificar que CI pasa
4. Desplegar frontend en Vercel (push automatico)
5. Desplegar backend con `sam deploy`
6. Verificar URLs publicas
7. Grabar video demo final
8. Compartir el repo

**Exito!**
