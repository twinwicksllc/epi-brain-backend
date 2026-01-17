# Setting up pgvector on Render.com

## Quick Setup

### Step 1: Enable pgvector in Render Dashboard

1. Go to your Render dashboard
2. Navigate to your PostgreSQL database
3. Click on the "Extensions" tab
4. Find `pgvector` in the list
5. Click "Enable"

### Step 2: Alternative - Add to render.yaml

```yaml
databases:
  - name: epi-brain-db
    databaseName: epi_brain
    user: epi_brain
    extensions:
      - pgvector
```

## Verify pgvector is Working

Run the setup script on your production database:

```bash
# Set your production DATABASE_URL
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'

# Run the setup script
python scripts/setup_pgvector.py
```

Expected output:
```
============================================================
pgvector Extension Setup
============================================================
Database: host:5432/dbname

PostgreSQL: PostgreSQL 15.x...

pgvector available: vector
Installed: 0.5.0

Already installed and enabled
Test passed!

pgvector setup complete!
Ready to build semantic memory!
```

## What pgvector Provides

- **Vector columns**: Store embeddings as vectors
- **Similarity search**: Find similar vectors efficiently
- **Indexes**: IVFFlat and HNSW indexes for fast queries
- **Distance operators**: `<->`, `<=>`, `<#>` for different distance metrics

## Common Issues

### "pgvector is NOT installed"
- Solution: Enable the extension in Render dashboard
- Contact Render support if you don't see it in the list

### "Permission denied"
- You need superuser privileges to install extensions
- On Render, the database owner has these privileges
- If issues persist, contact Render support

### "function ivfflat does not exist"
- Ensure you're using PostgreSQL 12+
- pgvector requires PostgreSQL 11+, IVFFlat requires 12+

## Development with SQLite

Since you're using SQLite locally:

**Option 1: Docker PostgreSQL (Recommended for Testing)**
```bash
docker run --name epi-brain-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=epi_brain \
  -p 5432:5432 \
  -v pgvector_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/epi_brain'
```

**Option 2: Mock Implementation**
- Build the semantic memory system
- Use mock/fake embeddings locally
- Test real functionality on Render

## Next Steps

Once pgvector is enabled:
1. Create semantic memory tables
2. Implement embedding generation
3. Build memory extraction and retrieval
4. Integrate with Persona Router