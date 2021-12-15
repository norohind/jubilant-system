squads_by_tag_short_pretty_keys = """select 
    name as "Squadron name",
    tag as "Tag",
    member_count as "Members",
    owner_name as "Owner",
    platform as "Platform",
    created as "Created UTC",
    power_name as "Power name",
    super_power_name as "Super power name",
    faction_name as "Faction name",
    --user_tags as "User tags",
    inserted_timestamp as "Updated UTC",
    squad_id
from squads_view
where tag = :tag
order by platform;
"""

squads_by_tag_short_raw_keys = """select 
    name,
    tag,
    member_count,
    owner_name,
    platform,
    created,
    power_name,
    super_power_name,
    faction_name,
    --user_tags,
    inserted_timestamp,
    squad_id
from squads_view
where tag = :tag
order by platform;
"""

squads_by_tag_extended_pretty_keys = """select 
    name as "Squadron name",
    tag as "Tag",
    member_count as "Members",
    owner_name as "Owner",
    platform as "Platform",
    created as "Created UTC",
    power_name as "Power name",
    super_power_name as "Super power name",
    faction_name as "Faction name",
    user_tags as "User tags",
    inserted_timestamp as "Updated UTC",
    squad_id,
    owner_id
from squads_view
where tag = :tag
order by platform;
"""

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
