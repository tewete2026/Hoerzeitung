-->=1.1.15
EXC:tUser_fav.sql
EXC:_Config.sql
alter table tUser add column `lastVersion` varchar(20) default '0.0.0' comment 'Letzte Version, die der User gelesen hat';
update tUser set lastVersion='0.0.0';
-->=1.1.17
update tUser set lastVersion=replace(lastVersion,'.','');
alter table tUser modify column `lastVersion` int unsigned default 0 COMMENT 'Letzte Version, die der User gelesen hat';
