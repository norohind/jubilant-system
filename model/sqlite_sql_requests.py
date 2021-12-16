squads_by_tag_extended_raw_keys = """select 
    name,
    tag,
    member_count,
    owner_name,
    owner_id,
    platform,
    created,
    power_name,
    super_power_name,
    faction_name,
    user_tags,
    inserted_timestamp,
    squad_id
from squads_view
where tag = :tag
order by platform;
"""

select_latest_motd_by_id = """select 
    motd, 
    date, 
    author 
from news 
where 
    squad_id = :squad_id and 
    type_of_news = 'public_statements' and 
    category = 'Squadrons_History_Category_PublicStatement' 
order by date desc 
limit 1;"""

select_nickname_by_fid_news_based = """select 
    author 
from news 
where cmdr_id = :fid 
order by date desc 
limit 1;"""
