-- Enable the pgvector extension (needed for embeddings)
create extension if not exists vector;

-- Table to store uploaded documents
create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    filename text not null,
    created_at timestamp with time zone default now()
);

-- Table to store text chunks and embeddings
create table if not exists chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade,
    chunk_index int not null,
    content text not null,
    embedding vector(384), -- match your SentenceTransformer dimension
    created_at timestamp with time zone default now()
);

-- Create a vector index for efficient similarity search
create index if not exists idx_chunks_embedding
on chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Optional: also index document_id for fast lookup
create index if not exists idx_chunks_document_id
on chunks (document_id);

-- Create storage bucket for files (optional)
insert into storage.buckets (id, name, public)
values ('rag-files', 'rag-files', false)
on conflict (id) do nothing;