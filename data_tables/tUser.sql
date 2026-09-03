/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.6-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: nhz
-- ------------------------------------------------------
-- Server version	11.8.6-MariaDB-5ubuntu0.1 from Ubuntu

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `tUser`
--

DROP TABLE IF EXISTS `tUser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tUser` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pnr` smallint(5) unsigned NOT NULL DEFAULT 0 COMMENT 'Persönliche Nummer',
  `seclevel` smallint(5) unsigned NOT NULL DEFAULT 0 COMMENT 'Berechtigungs Ebene',
  `pnrcreate` smallint(5) unsigned NOT NULL DEFAULT 0 COMMENT 'Persönliche Konto Nummer erstellt',
  `histid` int(11) DEFAULT NULL COMMENT 'ID zu tHistory',
  `freecode` varchar(20) NOT NULL DEFAULT '' COMMENT 'Freischaltcode',
  `active` bit(1) NOT NULL DEFAULT b'1' COMMENT 'Ist der Freischaltcode aktiv (1=J/0=N)',
  `guest` bit(1) NOT NULL DEFAULT b'0' COMMENT 'Ist der Freischaltcode ein Gast (1=J/0=N)',
  `createDate` date NOT NULL DEFAULT curdate() COMMENT 'Erstellungs Datum',
  `lastActive` date DEFAULT NULL COMMENT 'Letztes Datum Aktivität',
  `lastVersion` int(10) unsigned DEFAULT 0 COMMENT 'Letzte Version, die der User gelesen hat',
  PRIMARY KEY (`id`),
  UNIQUE KEY `pnr` (`pnr`),
  UNIQUE KEY `freecode` (`freecode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
INSERT INTO `tUser`(pnr,seclevel,histid,freecode,guest) VALUES (1,4,1,'4AQPW-LVB1-9E24-B7CG',0),(2,0,1,'0GAST-ABCD-ABCD-ABCD',1);
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-09-03 18:55:23
