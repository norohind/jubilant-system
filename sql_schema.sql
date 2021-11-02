create table if not exists squads_states (
squad_id int not null,
name text,
tag text,
owner_name text,
owner_id int,
platform text,
created text,
created_ts int,
accepting_new_members bool,
power_id int,
power_name text,
super_power_id int,
super_power_name text,
faction_id int,
faction_name text,
user_tags text,
member_count int,
pending_count int,
full bool,
public_comms bool,
public_comms_override bool,
public_comms_available bool,
current_season_trade_score int,
previous_season_trade_score int,
current_season_combat_score int,
previous_season_combat_score int,
current_season_exploration_score int,
previous_season_exploration_score int,
current_season_cqc_score int,
previous_season_cqc_score int,
current_season_bgs_score int,
previous_season_bgs_score int,
current_season_powerplay_score int,
previous_season_powerplay_score int,
current_season_aegis_score int,
previous_season_aegis_score int,
inserted_timestamp datetime default current_timestamp);

create view if not exists squads_view
as
select squad_id,
name,
tag,
owner_name,
owner_id,
platform,
created,
created_ts,
accepting_new_members,
power_id,
power_name,
super_power_id,
super_power_name,
faction_id,
faction_name,
user_tags,
member_count,
pending_count,
full,
public_comms,
public_comms_override,
public_comms_available,
current_season_trade_score,
previous_season_trade_score,
current_season_combat_score,
previous_season_combat_score,
current_season_exploration_score,
previous_season_exploration_score,
current_season_cqc_score,
previous_season_cqc_score,
current_season_bgs_score,
previous_season_bgs_score,
current_season_powerplay_score,
previous_season_powerplay_score,
current_season_aegis_score,
previous_season_aegis_score, max(inserted_timestamp) as inserted_timestamp from squads_states group by squad_id having tag is not null;

create table if not exists news (
squad_id int,
type_of_news text,
news_id int,
date int,
category text,
activity text,
season int,
bookmark text,
motd text,
author text,
cmdr_id int,
user_id int,
inserted_timestamp datetime default current_timestamp);

create view if not exists news_view
as
select *
from news
where inserted_timestamp in (
    select max(inserted_timestamp)
    from news
    group by squad_id)
group by squad_id;

create index if not exists idx_squads_states_0 on squads_states (squad_id);

create view if not exists squads_view_2
as
select squad_id,
name,
tag,
owner_name,
owner_id,
platform,
created,
created_ts,
accepting_new_members,
power_id,
power_name,
super_power_id,
super_power_name,
faction_id,
faction_name,
user_tags,
member_count,
pending_count,
full,
public_comms,
public_comms_override,
public_comms_available,
current_season_trade_score,
previous_season_trade_score,
current_season_combat_score,
previous_season_combat_score,
current_season_exploration_score,
previous_season_exploration_score,
current_season_cqc_score,
previous_season_cqc_score,
current_season_bgs_score,
previous_season_bgs_score,
current_season_powerplay_score,
previous_season_powerplay_score,
current_season_aegis_score,
previous_season_aegis_score,
current_season_trade_score +
current_season_combat_score +
current_season_exploration_score +
current_season_cqc_score +
current_season_bgs_score +
current_season_powerplay_score +
current_season_aegis_score as current_season_score,
previous_season_trade_score +
previous_season_combat_score +
previous_season_exploration_score +
previous_season_cqc_score +
previous_season_bgs_score +
previous_season_powerplay_score +
previous_season_aegis_score as previous_season_score, max(inserted_timestamp) as inserted_timestamp from squads_states group by squad_id having tag is not null;