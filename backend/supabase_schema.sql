-- Table to store uploaded documents
create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    filename text not null,
    created_at timestamp with time zone default now()
);

-- Table to store text chunks and embeddings as JSON
create table if not exists chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade,
    chunk_index int not null,
    content text not null,
    embedding jsonb not null, -- store embeddings as JSON arrays
    created_at timestamp with time zone default now()
);

-- Index for fast lookup by document_id
create index if not exists idx_chunks_document_id
on chunks (document_id);
