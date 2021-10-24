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
select *
from squads_states
where inserted_timestamp in (
    select max(inserted_timestamp)
    from squads_states
    group by squad_id)
group by squad_id;

create table if not exists news (
squad_id int,
type_of_news text,
news_id int,
date int,
category text,
activity text,
season text,
bookmark text,
motd text,
author text,
cmdr_id int,
user_id int,
inserted_timestamp datetime default current_timestamp);
