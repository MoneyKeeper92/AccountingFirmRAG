-- Tesón MVP · Supabase schema
-- Run once in Supabase → SQL Editor → New query → paste → Run.
-- The browser app uses the public "anon" key. Anon may INSERT events and
-- nothing else, so nobody can read other users' data from the browser.
-- You (and Claude, with the service key or the dashboard) read the data.

create table if not exists public.events (
  id           bigint generated always as identity primary key,
  received_at  timestamptz not null default now(),
  client_ts    timestamptz,
  uid          text,          -- random pseudonymous id (null if the user declined analytics)
  session_id   text,
  type         text not null,
  payload      jsonb not null default '{}'::jsonb,
  app_version  text
);

create index if not exists events_type_idx on public.events (type, received_at desc);
create index if not exists events_uid_idx  on public.events (uid, received_at desc);

alter table public.events enable row level security;

drop policy if exists "anon can insert events" on public.events;
create policy "anon can insert events"
  on public.events for insert
  to anon
  with check (
    char_length(type) between 1 and 64
    and (uid is null or char_length(uid) <= 64)
    and (session_id is null or char_length(session_id) <= 64)
    and pg_column_size(payload) <= 8000
  );
-- No select/update/delete policies for anon: inserts only.
revoke all on public.events from anon, authenticated;
grant insert on public.events to anon;

-- ── Handy views for the weekly review (dashboard / SQL editor) ──────────

create or replace view public.v_reports as
select received_at, payload->>'qid' as qid, payload->>'reason' as reason, payload->>'text' as detail, uid
from public.events where type = 'question_reported' order by received_at desc;

create or replace view public.v_feedback as
select received_at, (payload->>'rating')::int as rating, payload->>'text' as text, payload->>'email' as email,
       (payload->>'tests')::int as tests_done, uid
from public.events where type = 'feedback_sent' order by received_at desc;

create or replace view public.v_nps as
select received_at, (payload->>'score')::int as score, payload->>'why' as why, uid
from public.events where type = 'nps_submitted' order by received_at desc;

create or replace view public.v_onboarding as
select received_at, payload->>'exam' as exam, payload->>'cuando' as cuando, payload->>'academia' as academia,
       payload->>'academia_nombre' as academia_nombre, payload->>'fuente' as fuente, payload->'src' as src, uid
from public.events where type = 'onboarding_completed' order by received_at desc;

create or replace view public.v_question_health as
select payload->>'qid' as qid,
       count(*) as attempts,
       round(100.0 * avg(case when payload->>'result' = 'correct' then 1 else 0 end), 1) as pct_correct,
       round(100.0 * avg(case when payload->>'result' = 'blank' then 1 else 0 end), 1) as pct_blank,
       percentile_cont(0.5) within group (order by (payload->>'time_ms')::numeric) as median_ms
from public.events where type = 'question_answered'
group by 1 order by pct_correct asc;

create or replace view public.v_daily as
select date_trunc('day', received_at)::date as day,
       count(distinct uid) filter (where uid is not null) as active_users,
       count(*) filter (where type = 'question_answered') as answers,
       count(*) filter (where type = 'test_completed') as tests_completed,
       count(*) filter (where type = 'consent_given') as new_consenting_users
from public.events group by 1 order by 1 desc;

create or replace view public.v_tema_interest as
select payload->>'tema' as tema, count(*) filter (where (payload->>'on')::boolean) as votes
from public.events where type = 'tema_interest' group by 1 order by 2 desc;

-- Views are not exposed to anon: revoke to be explicit.
revoke all on public.v_reports, public.v_feedback, public.v_nps, public.v_onboarding,
              public.v_question_health, public.v_daily, public.v_tema_interest from anon, authenticated;
