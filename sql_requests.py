insert_squad_states: str = """insert into squads_states (
    squad_id, 
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
    previous_season_aegis_score) 
values  (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

insert_news: str = """insert into news (
squad_id,
type_of_news,
news_id,
date,
category,
activity,
season,
bookmark,
motd,
author,
cmdr_id,
user_id)
values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

check_if_squad_exists_in_db: str = """select count(*) 
from squads_states
where squad_id = ?;"""

properly_delete_squad: str = """insert into squads_states (squad_id) values (?);"""

check_if_we_already_deleted_squad_in_db: str = """select count(*) 
from squads_states 
where squad_id = ? and tag is null"""

select_last_known_id: str = """select squad_id 
from squads_states 
order by squad_id desc
limit 1;"""

select_squads_to_update: str = """select squad_id 
from squads_view
where tag is not null 
order by inserted_timestamp asc
limit ?;"""

select_first_hole_id: str = """select squad_id+1 as a 
from squads_states except 
    select squad_id 
    from squads_states 
    order by a asc 
    limit 1;"""

select_old_new: str = """select {column}
from squads_states
where squad_id = ?
order by inserted_timestamp desc
limit 2;"""

# AAAAAAAAA, it require to do something with it
select_old_new_news: str = """select {column} 
from squads_states inner join news on
    squads_states.squad_id = news.squad_id
     and substr(squads_states.inserted_timestamp, 1, 16) = substr(news.inserted_timestamp, 1, 16) 
where category = 'Squadrons_History_Category_PublicStatement' and squads_states.squad_id = ? 
order by squads_states.inserted_timestamp
limit 2;"""

select_important_before_delete: str = """select name, platform, member_count, tag, user_tags 
from squads_view 
where squad_id = ?;"""