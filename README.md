# 🚀 Portal de Aprovação de Custos Extras - Linea Alimentos

Sistema especializado na gestão e auditoria de solicitações de custos extras para transportadoras, inspirado em ferramentas de governança como GLPI, com fluxo de aprovação dinâmico, visão de BI e histórico imutável.

---

## 🎯 Objetivo

Centralizar, controlar e auditar solicitações de custos extras realizadas por transportadoras, garantindo:

- **Rastreabilidade:** Monitoramento total desde a abertura até o faturamento.
- **Controle de SLA:** Meta de conclusão em 48 horas (2 dias).
- **Histórico Imutável:** Registro de cada alteração de status para conformidade.
- **Comunicação e Fluxo:** Interface clara para validação e faturamento.

---

## 🧱 Arquitetura

- **Frontend**: Streamlit
- **Autenticação**: Supabase Auth
- **Banco de Dados**: Supabase PostgreSQL
- **Armazenamento**: Supabase Storage
- **Deploy**: Render / Streamlit Cloud
- **Versionamento**: GitHub

---

## 👥 Tipos de Usuário

### 1️⃣ Transportador
- Abre solicitações de custo extra anexando dados da NF.
- Acompanha status no dashboard pessoal.
- Corrige solicitações marcadas como "Pendente Transportador".
- Visualiza apenas suas próprias solicitações (Segurança RLS).

### 2️⃣ Torre de Controle (Validação)
- Visualiza todas as solicitações da operação.
- Valida documentos e informações técnicas.
- Pode aprovar, recusar ou solicitar ajustes.
- **Obrigatório** inserir observação ao alterar status.

### 3️⃣ Administrador (Gestão e Finanças)
- Gerencia usuários e permissões.
- Visualiza dashboard de BI estratégico.
- Realiza o faturamento e finaliza as solicitações.
- Controle total do ciclo de vida dos dados.

---

## 🔄 Workflow de Status

O sistema monitora o tempo de resposta com meta de **48 horas (2 dias)** para encerramento.

| Status | Descrição |
|:--- |:--- |
| **Aberto** | Solicitação criada pelo transportador. |
| **Em Validação** | Em análise técnica pela Torre de Controle. |
| **Pendente Transportador** | Necessita de correção ou complemento do transportador. |
| **Aprovado** | Validado e pronto para a fila de faturamento. |
| **Recusado** | Solicitação negada (justificativa obrigatória). |
| **Em Faturamento** | Processo financeiro em andamento. |
| **Finalizado** | Processo faturado e encerrado. |

---

## 📝 Formulário de Solicitação

Campos obrigatórios capturados:
- Número da Nota Fiscal
- Nome do Cliente
- Tipo de Custo Extra (Estadia, Devolução, Reentrega, etc.)
- Valor do Custo Extra
- Data de Emissão e Entrega da NF
- Comprovante (Upload de PDF ou JPG)

> A transportadora é identificada automaticamente através do e-mail do usuário logado.

---

## 📊 Dashboards e BI

O sistema conta com uma torre de controle interativa (`gestao.py`):
- **Visão em Dias:** Eixos X e Y configurados para escala diária.
- **KPIs de Performance:** Total aprovado, SLA médio em dias e taxa de recusa.
- **Análise de Lead Time:** Gráfico de dispersão com linha de meta (meta 2 dias).
- **Filtros Estratégicos:** Por período (Data Início/Fim) e por Transportador.

---

## 📜 Histórico e Auditoria

Cada solicitação mantém um histórico completo e auditável na tabela `historico`:
- **Status na Época:** Registro do estado da transição.
- **Usuário Responsável:** E-mail de quem realizou a alteração.
- **Data e Hora:** Registro preciso (convertido para Horário de Brasília).
- **Observação:** Detalhamento do motivo da mudança.

> **Nota:** Nenhuma informação é apagada do banco; todas as transições são incrementais.

---

## 🔐 Controle de Acesso

- **Nível de Banco:** Utilização de Row Level Security (RLS) no Supabase.
- **Restrição de Papéis:** Constraint `profiles_role_check` garante que apenas roles válidas (admin, validador, transportador) existam no sistema.
- **Segurança de Segredos:** Credenciais de API protegidas via `secrets.toml`.

---

## 📦 Estrutura do Repositório

```text
Approval_flow/
├── app.py                # Entrada principal e Navegação
├── src/
│   ├── database.py       # Conexão com Supabase SDK
│   └── auth.py           # Lógica de login e sessão
├── gestao.py             # Módulo de BI e Gestão de SLA
├── pages/                # Telas divididas por perfil
│   ├── transportador/
│   ├── validacao/
│   └── admin/
├── .streamlit/
│   └── secrets.toml      # Configurações locais (Não versionado)
├── requirements.txt      # Dependências do projeto
└── README.md             # Documentação
