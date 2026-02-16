-- ResearchGraph Database Schema
-- PostgreSQL with pgvector for semantic search

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================
-- Table: papers
-- Stores paper metadata from arXiv
-- ============================================
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxiv_id VARCHAR(32) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    authors JSONB DEFAULT '[]',
    categories JSONB DEFAULT '[]',
    published_date TIMESTAMPTZ,
    updated_date TIMESTAMPTZ,
    pdf_url TEXT,
    local_pdf_path TEXT,

    -- Citation graph data ("references" is a reserved word, must be quoted)
    "references" JSONB DEFAULT '[]',
    cited_by JSONB DEFAULT '[]',

    -- Processing status
    is_processed BOOLEAN DEFAULT FALSE,
    chunk_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast arXiv ID lookups
CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_papers_created_at ON papers(created_at DESC);

-- ============================================
-- Table: paper_chunks
-- Stores text chunks with vector embeddings
-- ============================================
CREATE TABLE IF NOT EXISTS paper_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,

    -- Chunk content
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,

    -- Metadata about the chunk location
    page_number INTEGER,
    section_title TEXT,

    -- Vector embedding (Gemini text-embedding-004 = 768 dimensions)
    embedding vector(768),

    -- Token count for context window management
    token_count INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (IVFFlat)
-- IVFFlat needs existing rows to build; wrap in exception handler so it
-- doesn't block the rest of the migration on an empty table.
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_paper_chunks_embedding
        ON paper_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
EXCEPTION WHEN others THEN
    RAISE NOTICE 'IVFFlat index skipped (likely empty table): %', SQLERRM;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_paper_chunks_paper_id ON paper_chunks(paper_id);

-- ============================================
-- Table: chat_cache
-- Stores Q&A pairs to prevent redundant LLM calls
-- ============================================
CREATE TABLE IF NOT EXISTS chat_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,

    -- The question (normalized for matching)
    question TEXT NOT NULL,
    question_hash VARCHAR(64) NOT NULL,  -- SHA-256 for fast lookup

    -- The generated answer
    answer TEXT NOT NULL,

    -- Context chunks used (for transparency)
    context_chunk_ids JSONB DEFAULT '[]',

    -- LLM metadata
    model_used VARCHAR(64),
    tokens_used INTEGER,

    -- Cache metadata
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint for cache lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_cache_lookup
    ON chat_cache(paper_id, question_hash);
CREATE INDEX IF NOT EXISTS idx_chat_cache_paper_id ON chat_cache(paper_id);

-- ============================================
-- Table: ingestion_jobs
-- Tracks paper ingestion status
-- ============================================
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxiv_id VARCHAR(32) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_arxiv_id ON ingestion_jobs(arxiv_id);

-- ============================================
-- Helper Functions
-- ============================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for papers table
DROP TRIGGER IF EXISTS update_papers_updated_at ON papers;
CREATE TRIGGER update_papers_updated_at
    BEFORE UPDATE ON papers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to search similar chunks by embedding
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(768),
    target_paper_id UUID,
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    chunk_id UUID,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pc.id,
        pc.content,
        1 - (pc.embedding <=> query_embedding) as similarity
    FROM paper_chunks pc
    WHERE pc.paper_id = target_paper_id
      AND 1 - (pc.embedding <=> query_embedding) > match_threshold
    ORDER BY pc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Function to increment cache hit count
CREATE OR REPLACE FUNCTION increment_cache_hit(cache_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE chat_cache
    SET hit_count = hit_count + 1,
        last_accessed_at = NOW()
    WHERE id = cache_id;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO researchgraph;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO researchgraph;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO researchgraph;
