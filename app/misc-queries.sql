select * from bot_quote join tag_associations on bot_quote_id=bot_quote.id join tag on tag.id=tag_associations.tag_id limit 1;

select tag.name, count(*), max(bq.created_on) from bot_quote bq join tag_associations on bot_quote_id=bq.id join tag on tag.id=tag_associations.tag_id group by tag_id;
