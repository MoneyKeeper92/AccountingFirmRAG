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

-- ── v0.2: learning model and the adaptive-practice experiment (adapt-v1) ──

-- Accuracy per concept (questions can carry several concepts).
create or replace view public.v_concept_accuracy as
select c.concept,
       count(*) as attempts,
       round(100.0 * avg(case when e.payload->>'result' = 'correct' then 1 else 0 end), 1) as pct_correct,
       count(distinct e.uid) as users
from public.events e
cross join lateral jsonb_array_elements_text(coalesce(e.payload->'concepts', '[]'::jsonb)) as c(concept)
where e.type = 'question_answered'
group by 1 order by pct_correct asc;

-- Which typical confusions students fall into most.
create or replace view public.v_misconceptions as
select payload->>'mis' as misconception, count(*) as hits, count(distinct uid) as users
from public.events where type = 'question_answered' and payload->>'mis' is not null
group by 1 order by hits desc;

-- One row per participant: arm, diagnostic (pre) and progress check (post) scores, practice volume.
create or replace view public.v_experiment as
with arm as (
  select distinct on (uid) uid, payload->>'arm' as arm, received_at as assigned_at
  from public.events where type = 'exp_assigned' and payload->>'exp' = 'adapt-v1'
  order by uid, received_at
), pre as (
  select distinct on (uid) uid, payload->>'form' as pre_form, (payload->>'score')::numeric as pre_score
  from public.events where type = 'checkpoint_completed' and payload->>'kind' = 'pre'
  order by uid, received_at
), post as (
  select distinct on (uid) uid, (payload->>'score')::numeric as post_score,
         (payload->>'practice_answers')::int as practice_answers, (payload->>'days_since_pre')::numeric as days_since_pre
  from public.events where type = 'checkpoint_completed' and payload->>'kind' = 'post'
  order by uid, received_at
)
select arm.uid, arm.arm, arm.assigned_at, pre.pre_form, pre.pre_score, post.post_score,
       post.post_score - pre.pre_score as gain, post.practice_answers, post.days_since_pre
from arm left join pre using (uid) left join post using (uid);

-- Summary by arm (only participants who completed both checkpoints).
create or replace view public.v_experiment_summary as
select arm,
       count(*) filter (where pre_score is not null) as did_pre,
       count(*) filter (where post_score is not null) as did_post,
       round(avg(pre_score) filter (where post_score is not null), 2) as avg_pre,
       round(avg(post_score), 2) as avg_post,
       round(avg(gain), 2) as avg_gain,
       round(stddev_samp(gain), 2) as sd_gain,
       round(avg(practice_answers), 0) as avg_practice
from public.v_experiment group by arm;

-- ── v0.3: student profiles (email sign-in with a one-time code) and AI focus plans ──
-- Emails live only in Supabase Auth (auth.users). profiles holds the synced learning state.

create table if not exists public.profiles (
  id                   uuid primary key references auth.users(id) on delete cascade,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  state                jsonb not null default '{}'::jsonb,   -- answers, concept stats, history (no email)
  marketing_opt_in     boolean not null default false,       -- weekly summary / convocatoria emails
  marketing_opt_in_at  timestamptz,
  plan                 jsonb,                                -- latest focus plan (written by the focus-plan function)
  plan_at              timestamptz
);
alter table public.profiles enable row level security;

drop policy if exists "own profile: read"   on public.profiles;
drop policy if exists "own profile: insert" on public.profiles;
drop policy if exists "own profile: update" on public.profiles;
drop policy if exists "own profile: delete" on public.profiles;
create policy "own profile: read"   on public.profiles for select to authenticated using (auth.uid() = id);
create policy "own profile: insert" on public.profiles for insert to authenticated with check (auth.uid() = id);
create policy "own profile: update" on public.profiles for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);
create policy "own profile: delete" on public.profiles for delete to authenticated using (auth.uid() = id);

-- Students may write their own state and email preference, never the plan (only the function writes it).
revoke all on public.profiles from anon, authenticated;
grant select, delete on public.profiles to authenticated;
grant insert (id, state, updated_at, marketing_opt_in, marketing_opt_in_at) on public.profiles to authenticated;
grant update (state, updated_at, marketing_opt_in, marketing_opt_in_at) on public.profiles to authenticated;

-- Every plan request, for cost tracking and for comparing AI plans with the rules fallback.
create table if not exists public.plans (
  id             bigint generated always as identity primary key,
  created_at     timestamptz not null default now(),
  user_id        uuid references auth.users(id) on delete cascade,
  source         text not null,            -- 'ai' | 'rules'
  model          text,
  plan           jsonb not null,
  summary        jsonb,                    -- the anonymised learning summary sent to the model
  input_tokens   integer,
  output_tokens  integer,
  latency_ms     integer,
  error          text                      -- why the rules fallback was used, if it was
);
create index if not exists plans_user_idx on public.plans (user_id, created_at desc);
create index if not exists plans_day_idx  on public.plans (created_at desc, source);
alter table public.plans enable row level security;   -- no policies: only the service role reads or writes
revoke all on public.plans from anon, authenticated;

-- Weekly email list (run as the project owner in the SQL editor; never exposed to the app).
create or replace view public.v_marketing_list as
select u.email, p.marketing_opt_in_at, p.updated_at as last_active
from public.profiles p join auth.users u on u.id = p.id
where p.marketing_opt_in;

-- AI plan cost and fallback rate per day.
create or replace view public.v_plan_costs as
select date_trunc('day', created_at)::date as day, source, count(*) as plans,
       sum(input_tokens) as input_tokens, sum(output_tokens) as output_tokens,
       round(avg(latency_ms)) as avg_latency_ms,
       count(*) filter (where error is not null) as with_error
from public.plans group by 1, 2 order by 1 desc, 2;

-- Views are not exposed to anon: revoke to be explicit.
revoke all on public.v_reports, public.v_feedback, public.v_nps, public.v_onboarding,
              public.v_question_health, public.v_daily, public.v_tema_interest,
              public.v_concept_accuracy, public.v_misconceptions, public.v_experiment, public.v_experiment_summary,
              public.v_marketing_list, public.v_plan_costs
         from anon, authenticated;
