squads_by_tag_extended_raw_keys = """select 
    name,
    tag,
    member_count,
    owner_name,
    owner_id,
    platform,
    created,
    null_fdev(power_name) as power_name,
    null_fdev(super_power_name) as super_power_name,
    null_fdev(faction_name) as faction_name,
    user_tags,
    max(inserted_timestamp) as inserted_timestamp,
    squad_id
from squads_states 
where tag = :tag 
and squad_id not in (select squad_id from squads_states where tag is null)
group by platform 
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
