-- TEAM狭気: 次回ルール決定権は、各モードで実際にごちそうした人へ渡す。
-- 狭気: 勝者 / 通常: 敗者。削除時は直前の支払者に戻す。

create or replace function public.kyoki_record_round(
  p_member_id bigint, p_event_date date, p_place text, p_amount integer,
  p_participants bigint[], p_winner_id bigint, p_loser_id bigint,
  p_note text, p_historical_mode text
) returns jsonb language plpgsql set search_path = '' as $function$
declare g record; m record; k text; pay_id bigint; r_id bigint;
begin
  select * into m from public.kyoki_members where id=p_member_id;
  if not found then raise exception 'ログインが無効です'; end if;
  select * into g from public.kyoki_groups where id=m.group_id for update;
  if p_amount is null or p_amount<1 or p_amount>100000000 then raise exception '会計金額を確認してください'; end if;
  if p_event_date is null or p_event_date>((now() at time zone 'Asia/Tokyo')::date+1) then raise exception '開催日を確認してください'; end if;
  if cardinality(p_participants)<2 or cardinality(p_participants)>60
     or (select count(distinct n) from unnest(p_participants) as n)<>cardinality(p_participants)
     or not(p_winner_id=any(p_participants)) or not(p_loser_id=any(p_participants))
     or p_winner_id=p_loser_id then raise exception '支払者と奢ってもらう人を確認してください'; end if;
  if (select count(*) from public.kyoki_members where group_id=m.group_id and id=any(p_participants))<>cardinality(p_participants) then raise exception '所属していないメンバーが含まれます'; end if;
  if length(coalesce(p_place,''))>80 or length(coalesce(p_note,''))>500 then raise exception '文字数制限を超えています'; end if;
  if p_historical_mode is null then
    k:=g.next_mode;
    if k is null then raise exception '前回のごちそうする人がルールを選ぶまで記録できません'; end if;
  else
    if m.role<>'admin' then raise exception '過去データの登録は管理者のみ'; end if;
    k:=p_historical_mode;
  end if;
  if k not in('otoko','normal') then raise exception 'ルールが正しくありません'; end if;
  pay_id:=case when k='otoko' then p_winner_id else p_loser_id end;
  insert into public.kyoki_rounds(group_id,event_date,place,amount,mode,winner_id,loser_id,payer_id,participants,note,is_historical,recorded_by)
  values(m.group_id,p_event_date,coalesce(p_place,''),p_amount,k,p_winner_id,p_loser_id,pay_id,p_participants,coalesce(p_note,''),p_historical_mode is not null,p_member_id)
  returning id into r_id;
  if p_historical_mode is null then
    update public.kyoki_groups set next_mode=null,next_decider_id=pay_id where id=g.id;
  end if;
  return jsonb_build_object('ok',true,'id',r_id,'payer_id',pay_id,'next_decider_id',pay_id);
end $function$;

create or replace function public.kyoki_delete_round(p_member_id bigint,p_round_id bigint)
returns jsonb language plpgsql set search_path = '' as $function$
declare g record; m record; r record; latest bigint; prev_payer bigint;
begin
  select * into m from public.kyoki_members where id=p_member_id;
  if m.role is distinct from 'admin' then raise exception '管理者だけが削除できます'; end if;
  select * into g from public.kyoki_groups where id=m.group_id for update;
  select * into r from public.kyoki_rounds where id=p_round_id and group_id=g.id;
  if not found then raise exception '記録がありません'; end if;
  if not r.is_historical then
    select id into latest from public.kyoki_rounds where group_id=g.id and not is_historical order by id desc limit 1;
    if r.id<>latest then raise exception '通常記録は最新分から削除してください'; end if;
  end if;
  delete from public.kyoki_rounds where id=r.id;
  if not r.is_historical then
    select payer_id into prev_payer from public.kyoki_rounds where group_id=g.id and not is_historical order by id desc limit 1;
    if prev_payer is null then
      select id into prev_payer from public.kyoki_members where group_id=g.id and role='admin' order by id limit 1;
    end if;
    update public.kyoki_groups set next_decider_id=prev_payer,next_mode=null where id=g.id;
  end if;
  return jsonb_build_object('ok',true,'next_decider_id',prev_payer);
end $function$;
