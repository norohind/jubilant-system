squads_by_tag = """select 
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
where tag = :tag;
"""

squads_by_tag_extended = """select 
    name as "Squadron name",
    tag as "Tag",
    member_count as "Members",
    owner_name as "Owner",
    platform as "Platform",
    created as "Created UTC",
    power_name as "Power name",
    super_power_name as "Super power name",
    faction_name as "Faction name",
    user_tags,
    inserted_timestamp as "Updated UTC",
    squad_id
from squads_view
where tag = :tag;
"""