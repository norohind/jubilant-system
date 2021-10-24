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