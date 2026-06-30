/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: bv
-- ------------------------------------------------------
-- Server version	11.8.3-MariaDB-1build1 from Ubuntu

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

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
DROP TABLE IF EXISTS `tUser`;
CREATE TABLE `tUser` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pnr` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Persönliche Nummer',
  `seclevel` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Berechtigungs Ebene',
  `pnrcreate` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Persönliche Nummer erstellt',
  `histid` int(11) DEFAULT NULL COMMENT 'ID zu tHistory',
  `freecode` varchar(20) NOT NULL DEFAULT '' COMMENT 'Freischaltcode',
  `active` bit(1) NOT NULL DEFAULT b'1' COMMENT 'Ist der Freischaltcode aktiv (1=J/0=N)',
  `createDate` datetime NOT NULL DEFAULT current_timestamp COMMENT 'Erstellungs Datum',
  `lastActive` datetime DEFAULT NULL COMMENT 'Letztes Datum Aktivität',
  PRIMARY KEY (`id`),
  UNIQUE KEY `pnr` (`pnr`),
  UNIQUE KEY `freecode` (`freecode`)
) ENGINE=InnoDB AUTO_INCREMENT=1987 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
TRUNCATE TABLE `tUser`;
INSERT INTO `tUser`(pnr,seclevel,histid,freecode) VALUES(1,4,1,'AQPW-LVB1-9E24-B7CG');
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-05-16 18:40:45
