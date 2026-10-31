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
-- Table structure for table `tChapter`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
DROP TABLE IF EXISTS `tChapter`;
CREATE TABLE `tChapter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `albumId` int(11) COMMENT 'Zugehörige ID des Albums',
  `seclevel` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Berechtigungs Ebene',
  `pnr` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Persönliche Konto Nummer',
  `title` varchar(255) NOT NULL DEFAULT '' COMMENT 'Titel des Beitrags',
  `track` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Track-Nummer des Titels',
  `author` varchar(50) NOT NULL DEFAULT '' COMMENT 'Urheberrechtlicher Autor',
  `source` varchar(50) NOT NULL DEFAULT '' COMMENT 'Quelle der Vorlage',
  `reader` varchar(50) NOT NULL DEFAULT '' COMMENT 'Vorleser des Artikels',
  `summary` text NOT NULL DEFAULT '' COMMENT 'Beschreibung des Beitrags',
  `media` varchar(255) NOT NULL DEFAULT '' COMMENT 'Medien Datei',
  `duration` varchar(10) NOT NULL DEFAULT '' COMMENT 'Spiellänge der Medien Datei',
  `publicationDate` datetime NOT NULL DEFAULT current_timestamp() COMMENT 'Veröffentlichungs Datum',
  `sourceDate` date NOT NULL DEFAULT current_date() COMMENT 'Veröffentlichungs Datum der Quelle',
  `allowed` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Urheberrechtliche Erlaubnis',
  PRIMARY KEY (`id`),
  UNIQUE KEY `media` (`media`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
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
