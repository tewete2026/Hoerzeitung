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
-- Table structure for table `tLog`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
DROP TABLE IF EXISTS `tLog`;
CREATE TABLE `tLog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `seclevel` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Berechtigungs Ebene',
  `pnr` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'Persönliche Konto Nummer',
  `guest` bit(1) NOT NULL DEFAULT b'0' COMMENT 'Ist der Freischaltcode ein Gast (1=J/0=N)',
  `freecode` varchar(20) NOT NULL DEFAULT '' COMMENT 'Freischaltcode',
  `media` varchar(255) NOT NULL DEFAULT '' COMMENT 'Medien Datei',
  `accessDate` date NOT NULL DEFAULT curdate() COMMENT 'Zugriffs Datum',
  `accesscount` int unsigned NOT NULL DEFAULT 0 COMMENT 'Anzal der Zufriffe pro pnr,accessDate,media',
  KEY `pnr` (`pnr`),
  KEY `media` (`media`),
  KEY `accessDate` (`accessDate`),
  UNIQUE KEY `access` (`pnr`, `accessDate`, `media`),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1987 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
TRUNCATE TABLE `tLog`;
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
