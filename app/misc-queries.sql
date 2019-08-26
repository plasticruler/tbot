select * from bot_quote join tag_associations on bot_quote_id=bot_quote.id join tag on tag.id=tag_associations.tag_id limit 1;

select tag.name, count(*), max(bq.created_on) from bot_quote bq join tag_associations on bot_quote_id=bq.id join tag on tag.id=tag_associations.tag_id group by tag_id;


--get count by tag
 select ContentTag.name, count(*), max(ci.created_on) from ContentItem ci
 join contenttag_associations on contentitem_id=ci.id join ContentTag on ContentTag.id=contenttag_associations.contenttag_id 
 group by contenttag_id;