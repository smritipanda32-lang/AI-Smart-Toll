-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: ai_smart_toll
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `fraud_records`
--

DROP TABLE IF EXISTS `fraud_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fraud_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transaction_id` int NOT NULL,
  `fraud_type` varchar(100) DEFAULT NULL,
  `fraud_score` decimal(5,2) DEFAULT '0.00',
  `reason` varchar(255) DEFAULT NULL,
  `detected_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `transaction_id` (`transaction_id`),
  CONSTRAINT `fraud_records_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fraud_records`
--

LOCK TABLES `fraud_records` WRITE;
/*!40000 ALTER TABLE `fraud_records` DISABLE KEYS */;
INSERT INTO `fraud_records` VALUES (1,2,'Duplicate Transaction',85.00,'Possible duplicate transaction for the same vehicle and toll plaza.','2026-10-06 03:14:55'),(2,5,'Duplicate Transaction',85.00,'Possible duplicate transaction for the same vehicle and toll plaza.','2026-10-06 04:00:44'),(3,7,'Duplicate Transaction',85.00,'Possible duplicate transaction for the same vehicle and toll plaza.','2026-10-06 04:31:46'),(4,8,'Duplicate Transaction',85.00,'Possible duplicate transaction for the same vehicle and toll plaza.','2026-10-06 04:31:46'),(5,10,'Duplicate Transaction',85.00,'Possible duplicate transaction for the same vehicle and toll plaza.','2026-10-06 04:34:26'),(6,11,'Duplicate Transaction',85.00,'Possible duplicate transaction for the same vehicle and toll plaza.','2026-10-06 05:12:56'),(7,13,'Repeated Transaction',85.00,'Repeated vehicle transaction at the same toll plaza.','2026-10-12 13:52:09'),(8,15,'Repeated Transaction',85.00,'Repeated vehicle transaction at the same toll plaza within 30 minutes.','2026-10-12 14:03:25'),(9,18,'Repeated Transaction',85.00,'Repeated vehicle transaction at the same toll plaza within 30 minutes.','2026-10-29 16:45:07');
/*!40000 ALTER TABLE `fraud_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(150) NOT NULL,
  `message` varchar(255) NOT NULL,
  `notification_type` varchar(30) DEFAULT 'info',
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,'Transaction Verified','Vehicle MH14XY5678 was successfully recorded.','success',0,'2026-10-06 04:30:30'),(2,'Potential Fraud Detected','Possible duplicate transaction for the same vehicle and toll plaza.','danger',0,'2026-10-06 04:31:46'),(3,'Potential Fraud Detected','Possible duplicate transaction for the same vehicle and toll plaza.','danger',0,'2026-10-06 04:31:46'),(4,'Transaction Verified','Vehicle KA01AB5678 was successfully recorded.','success',0,'2026-10-06 04:33:50'),(5,'Potential Fraud Detected','Possible duplicate transaction for the same vehicle and toll plaza.','danger',0,'2026-10-06 04:34:26'),(6,'Potential Fraud Detected','Possible duplicate transaction for the same vehicle and toll plaza.','danger',0,'2026-10-06 05:12:56'),(7,'Transaction Recorded','Normal transaction recorded for vehicle MH23DE6532.','success',0,'2026-10-07 06:15:59'),(8,'Fraud Detected','Suspicious transaction detected for vehicle MH23DE6532 at Chennai Toll Plaza.','fraud',0,'2026-10-12 13:52:09'),(9,'Transaction Recorded','Normal transaction recorded for vehicle KA01AB5678.','success',0,'2026-10-12 14:03:25'),(10,'Fraud Detected','Suspicious transaction detected for vehicle KA01AB5678 at Mumbai Central.','fraud',0,'2026-10-12 14:03:25'),(11,'Transaction Recorded','Normal transaction recorded for vehicle MH12CD3456.','success',0,'2026-10-12 14:03:37'),(12,'Transaction Recorded','Normal transaction recorded for vehicle MH12CD3456.','success',0,'2026-10-29 16:44:56'),(13,'Fraud Detected','Suspicious transaction detected for vehicle MH12CD3456 at Nashik Toll Plaza.','fraud',0,'2026-10-29 16:45:07'),(14,'Transaction Recorded','Normal transaction recorded for vehicle KA01AB5678.','success',0,'2026-10-29 16:45:46'),(15,'Transaction Recorded','Normal transaction recorded for vehicle MH12CD3456.','success',0,'2026-10-30 14:29:07');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `toll_plazas`
--

DROP TABLE IF EXISTS `toll_plazas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `toll_plazas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plaza_name` varchar(100) NOT NULL,
  `location` varchar(150) DEFAULT NULL,
  `toll_amount` decimal(10,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `toll_plazas`
--

LOCK TABLES `toll_plazas` WRITE;
/*!40000 ALTER TABLE `toll_plazas` DISABLE KEYS */;
INSERT INTO `toll_plazas` VALUES (1,'Mumbai Central','Mumbai, Maharashtra',100.00,'2026-10-06 03:41:54'),(2,'Pune Expressway','Pune, Maharashtra',120.00,'2026-10-06 03:47:11'),(3,'Nashik Toll Plaza','Nashik, Maharashtra',90.00,'2026-10-06 03:50:21'),(4,'Chennai Toll Plaza','Chennai, Tamil Nadu',120.00,'2026-10-07 06:15:47');
/*!40000 ALTER TABLE `toll_plazas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vehicle_number` varchar(20) NOT NULL,
  `toll_plaza` varchar(100) NOT NULL,
  `transaction_amount` decimal(10,2) DEFAULT '0.00',
  `transaction_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(20) DEFAULT 'Normal',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
INSERT INTO `transactions` VALUES (1,'MH12AB1234','Mumbai Central',100.00,'2026-10-06 03:13:36','Normal'),(2,'MH12AB1234','Mumbai Central',100.00,'2026-10-06 03:14:55','Fraud'),(3,'KA01AB5678','Nashik Toll Plaza',100.00,'2026-10-06 03:57:48','Normal'),(4,'KA01AB5678','Pune Expressway',100.00,'2026-10-06 04:00:07','Normal'),(5,'KA01AB5678','Nashik Toll Plaza',100.00,'2026-10-06 04:00:44','Fraud'),(6,'MH14XY5678','Nashik Toll Plaza',100.00,'2026-10-06 04:30:30','Normal'),(7,'MH14XY5678','Nashik Toll Plaza',100.00,'2026-10-06 04:31:46','Fraud'),(8,'MH14XY5678','Nashik Toll Plaza',100.00,'2026-10-06 04:31:46','Fraud'),(9,'KA01AB5678','Mumbai Central',120.00,'2026-10-06 04:33:50','Normal'),(10,'KA01AB5678','Mumbai Central',120.00,'2026-10-06 04:34:26','Fraud'),(11,'KA01AB5678','Mumbai Central',100.00,'2026-10-06 05:12:56','Fraud'),(12,'MH23DE6532','Chennai Toll Plaza',120.00,'2026-10-07 06:15:59','Normal'),(13,'MH23DE6532','Chennai Toll Plaza',120.00,'2026-10-12 13:52:09','Fraud'),(14,'KA01AB5678','Mumbai Central',100.00,'2026-10-12 14:03:25','Normal'),(15,'KA01AB5678','Mumbai Central',100.00,'2026-10-12 14:03:25','Fraud'),(16,'MH12CD3456','Nashik Toll Plaza',90.00,'2026-10-12 14:03:37','Normal'),(17,'MH12CD3456','Nashik Toll Plaza',90.00,'2026-10-29 16:44:56','Normal'),(18,'MH12CD3456','Nashik Toll Plaza',90.00,'2026-10-29 16:45:07','Fraud'),(19,'KA01AB5678','Chennai Toll Plaza',120.00,'2026-10-29 16:45:46','Normal'),(20,'MH12CD3456','Mumbai Central',100.00,'2026-10-30 14:29:07','Normal');
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `role` varchar(20) DEFAULT 'operator',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'System Administrator','admin@toll.com','scrypt:32768:8:1$6TstZ11ZSsqfHZ1v$4560d9cae232a03914479ac4e1cf5b9b8943659d8c9e3230e36a98d87dcceb5ffb4a59497c080fd21b28ff3534ca0d221a7eff3e6cc522c0a2270f83c45d0a65','2026-10-06 02:58:49','admin'),(2,'Rahul Sharma','rahul.operator@smarttoll.com','scrypt:32768:8:1$5hfNDClYFf1nVRWU$ce87e6487a65986b72d1a7205060af41114f28d4ff5086fb4d6952084d3f7336302fdf635e14b97eba988ac897acf7a5012d86b37bbe03b161f54aa659d978dd','2026-10-08 14:44:16','operator'),(3,'Reema Sharma','reema.sharma.demo@gmail.com','scrypt:32768:8:1$VHeKGzUoIr7tD74P$89dfb61c8a91d1aa780ef98c4da61b0d25a719274446b99eabe26ead1d848a79b026b2e8389ece42855fb8ece21e7fadccb664c55a34b028a25b7b1535d03433','2026-10-30 12:58:02','operator');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vehicle_number` varchar(20) NOT NULL,
  `vehicle_type` varchar(50) DEFAULT NULL,
  `owner_name` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `vehicle_number` (`vehicle_number`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES (1,'MH14XY5678','Car','Rahul Sharma','2026-10-06 03:32:47'),(2,'KA01AB5678','Car','Dev Prakash','2026-10-06 03:49:50'),(3,'MH12CD3456','Car','Mira Desai','2026-10-06 04:56:52'),(4,'MH23DE6532','SUV','Rishi Dubey','2026-10-07 06:14:46');
/*!40000 ALTER TABLE `vehicles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-30 20:51:41
