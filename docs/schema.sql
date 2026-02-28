-- =========================================================
-- mistralhack – Supabase Postgres Schema
-- Run this in your Supabase SQL editor
-- =========================================================

-- Enable uuid generation
create extension if not exists "pgcrypto";

-- ── Users ──────────────────────────────────────────────
-- Extends Supabase auth.users with a public profile row.
create table if not exists public.users (
  id           uuid primary key references auth.users(id) on delete cascade,
  email        text unique not null,
  display_name text        not null,
  avatar_url   text,
  created_at   timestamptz default now()
);

-- Row-level security
alter table public.users enable row level security;

create policy "Users can read any profile"
  on public.users for select using (true);

create policy "Users can update own profile"
  on public.users for update using (auth.uid() = id);

-- Auto-insert profile row when auth user is created
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.users (id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();


-- ── Friends (symmetric) ────────────────────────────────
create table if not exists public.friendships (
  id          uuid primary key default gen_random_uuid(),
  user_a_id   uuid not null references public.users(id) on delete cascade,
  user_b_id   uuid not null references public.users(id) on delete cascade,
  created_at  timestamptz default now(),
  unique (user_a_id, user_b_id),
  check (user_a_id < user_b_id)  -- enforces row uniqueness regardless of order
);

alter table public.friendships enable row level security;

create policy "Users can see their own friendships"
  on public.friendships for select
  using (auth.uid() = user_a_id or auth.uid() = user_b_id);

create policy "Users can create friendships"
  on public.friendships for insert
  with check (auth.uid() = user_a_id or auth.uid() = user_b_id);


-- ── Presence ───────────────────────────────────────────
-- Updated by Electron app on heartbeat (every 30s)
create table if not exists public.presence (
  user_id      uuid primary key references public.users(id) on delete cascade,
  is_online    boolean     default false,
  last_seen_at timestamptz default now()
);

alter table public.presence enable row level security;

create policy "Anyone can read presence"
  on public.presence for select using (true);

create policy "Users can upsert own presence"
  on public.presence for upsert
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);


-- ── Pokes ──────────────────────────────────────────────
create table if not exists public.pokes (
  id                     uuid primary key default gen_random_uuid(),
  sender_id              uuid not null references public.users(id) on delete cascade,
  receiver_id            uuid not null references public.users(id) on delete cascade,
  timestamp              timestamptz default now(),
  classification         text check (classification in ('OFF_TASK', 'ON_TASK', 'UNKNOWN')),
  confidence             float,
  classification_reasoning text
);

alter table public.pokes enable row level security;

create policy "Poke sender or receiver can read"
  on public.pokes for select
  using (auth.uid() = sender_id or auth.uid() = receiver_id);

create policy "Authenticated users can insert pokes"
  on public.pokes for insert
  with check (auth.uid() = sender_id);


-- ── Feedback ───────────────────────────────────────────
create table if not exists public.feedback (
  id            uuid primary key default gen_random_uuid(),
  poke_id       uuid not null references public.pokes(id) on delete cascade,
  user_id       uuid not null references public.users(id) on delete cascade,
  user_feedback text not null check (user_feedback in ('CORRECT', 'WRONG_OFF_TASK', 'WRONG_ON_TASK')),
  comment       text,
  created_at    timestamptz default now()
);

alter table public.feedback enable row level security;

create policy "Users can read own feedback"
  on public.feedback for select
  using (auth.uid() = user_id);

create policy "Users can insert own feedback"
  on public.feedback for insert
  with check (auth.uid() = user_id);


-- ── Realtime ───────────────────────────────────────────
-- Enable realtime on pokes and presence tables
alter publication supabase_realtime add table public.pokes;
alter publication supabase_realtime add table public.presence;
