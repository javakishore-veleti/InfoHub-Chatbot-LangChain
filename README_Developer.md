# Developer Quick Reference

## Docker Services (Redis + Postgres)

```bash
npm run devops:docker:start-all      # Start Redis + Postgres containers
npm run devops:docker:stop-all       # Stop containers and remove network
npm run devops:docker:status-all     # Check container status
```

## API + UI

**Without Docker (SQLite, no Redis):**
```bash
npm run start:api-ui                 # bash
npm run start:api-ui:ps              # PowerShell
npm run stop:api-ui                  # bash  — stop API + UI
npm run stop:api-ui:ps               # PowerShell — stop API + UI
```

**With Docker backend (Postgres + Redis):**
```bash
npm run start:api-ui:docker          # bash
npm run start:api-ui:docker:ps       # PowerShell
npm run stop:api-ui:docker           # bash  — stop API + UI + Docker services
npm run stop:api-ui:docker:ps        # PowerShell — stop API + UI + Docker services
```

## Browser URLs

| Service | URL                          |
|---------|------------------------------|
| UI      | http://localhost:4200         |
| API     | http://localhost:8000         |
| API Docs| http://localhost:8000/docs    |
