# Portal de Aprovação de Custos Extras

Sistema de gestão de solicitações de custos extras para transportadoras, inspirado em ferramentas como GLPI, com fluxo de aprovação, validação, faturamento e histórico auditável.

---

## 🎯 Objetivo

Centralizar, controlar e auditar solicitações de custos extras realizadas por transportadoras, garantindo:

- Rastreabilidade
- Controle de acesso por perfil
- Histórico imutável
- Comunicação automática por e-mail
- Fluxo claro de aprovação e faturamento

---

## 🧱 Arquitetura

- **Frontend**: Streamlit
- **Autenticação**: Supabase Auth
- **Banco de Dados**: Supabase PostgreSQL
- **Armazenamento de Arquivos**: Supabase Storage
- **Deploy**: Render
- **Versionamento**: GitHub

---

## 👥 Tipos de Usuário

### 1️⃣ Transportador
- Abre solicitações de custo extra
- Acompanha status no dashboard
- Corrige solicitações quando pendentes
- Visualiza apenas suas próprias solicitações

### 2️⃣ Torre de Controle
- Visualiza todas as solicitações
- Valida documentos e informações
- Pode aprovar, recusar ou marcar como pendente
- Obrigatório inserir observação ao alterar status

### 3️⃣ Administrador
- Gerencia usuários
- Visualiza todas as solicitações
- Realiza faturamento
- Finaliza solicitações
- Controle total do sistema

---

## 🔄 Workflow de Status

| Status | Descrição |
|-----|---------|
| Aberto | Solicitação criada pelo transportador |
| Em Validação | Em análise pela torre de controle |
| Pendente Transportador | Necessita ajuste do transportador |
| Aprovado | Aprovado para faturamento |
| Recusado | Solicitação negada |
| Em Faturamento | Em processo financeiro |
| Finalizado | Faturado e encerrado |

---

## 📝 Formulário de Solicitação

Campos obrigatórios:
- Número da Nota Fiscal
- Nome do Cliente
- Tipo de Custo Extra
- Valor do Custo Extra
- Data de Emissão da Nota Fiscal
- Data de Entrega da Nota Fiscal

Campos condicionais:
- Comprovante (PDF ou JPG)

> A transportadora é identificada automaticamente pelo usuário logado.

---

## 📊 Dashboards

Todos os perfis possuem dashboards interativos com:
- Contadores por status
- Tabela de solicitações
- Filtros por status
- Acesso ao detalhe da solicitação

---

## 📜 Histórico e Auditoria

Cada solicitação mantém histórico completo de:
- Alterações de status
- Usuário responsável
- Data e hora
- Observações

Nenhuma informação é apagada.

---

## 🔐 Controle de Acesso

- Transportador: acesso apenas às próprias solicitações
- Torre de Controle: validação e análise
- Administrador: controle total e faturamento

---

## 📦 Estrutura do Repositório

```text
portal-aprovacao-custos/
├── app.py
├── auth/
├── pages/
│   ├── transportador/
│   ├── validacao/
│   └── admin/
├── services/
├── database/
├── utils/
└── README.md

