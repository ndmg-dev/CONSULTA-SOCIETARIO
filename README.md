# Consulta Societária — Mendonça Galvão Contadores Associados

<p align="center">
  <img src="frontend/public/logo.svg" alt="Mendonça Galvão" width="280">
</p>

<p align="center">
  <strong>Ferramenta de análise de CNPJ e estrutura de participação societária</strong>
</p>

---

## Sobre

Ferramenta interna do departamento societário da **Mendonça Galvão Contadores Associados** para consulta e análise de estruturas societárias de empresas brasileiras.

### Funcionalidades

- 🔍 **Consulta de CNPJ** — Busca dados cadastrais via BrasilAPI
- 👥 **Quadro Societário (QSA)** — Lista sócios e administradores
- 🏢 **Detecção de Sócios PJ** — Identifica sócios que são pessoas jurídicas
- 🌳 **Árvore de Participação** — Construção recursiva da árvore societária
- 🔄 **Detecção de Ciclos** — Identifica participações circulares
- 💾 **Cache Inteligente** — Armazena consultas para performance

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Python FastAPI |
| Banco de Dados | PostgreSQL 16 |
| API Externa | BrasilAPI (CNPJ) |
| Containerização | Docker + Docker Compose |

---

## Início Rápido

### Pré-requisitos

- Docker e Docker Compose instalados
- Node.js 20+ (para desenvolvimento local do frontend)
- Python 3.12+ (para desenvolvimento local do backend)

### Com Docker Compose (Recomendado)

```bash
# Clone e acesse o diretório
cd CONSULTA-SOCIETARIO

# Suba todos os serviços
docker-compose up --build

# Acesse
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Desenvolvimento Local

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Configure o banco PostgreSQL e a variável DATABASE_URL
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/cnpj/{cnpj}` | Consulta CNPJ e retorna dados + QSA |
| `GET` | `/api/cnpj/{cnpj}/ownership` | Consulta CNPJ com árvore de participação recursiva |

---

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL de conexão assíncrona do PostgreSQL |
| `CNPJ_API_BASE_URL` | `https://brasilapi.com.br/api/cnpj/v1` | URL base da API de CNPJ |
| `MAX_RECURSION_DEPTH` | `3` | Profundidade máxima da árvore societária |
| `CACHE_TTL_HOURS` | `24` | Tempo de vida do cache em horas |

---

## Identidade Visual

O design segue a identidade institucional da Mendonça Galvão:

- **Tema escuro premium** com fundo near-black
- **Glassmorfismo** com painéis translúcidos e backdrop blur
- **Ouro institucional** (#B89B64) como cor de destaque
- **Prata** (#D2D3D5) para tipografia secundária
- **Tipografia Inter** para legibilidade profissional

---

## Licença

Uso interno — Mendonça Galvão Contadores Associados © 2024
