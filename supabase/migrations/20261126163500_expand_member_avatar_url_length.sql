-- 写真アイコンは Supabase Storage の公開URLを保持するため、絵文字用の旧上限を拡張する。
alter table public.kyoki_members
  drop constraint if exists kyoki_members_avatar_length;

alter table public.kyoki_members
  add constraint kyoki_members_avatar_length
  check (char_length(avatar) >= 1 and char_length(avatar) <= 1024);
