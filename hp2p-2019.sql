-- --------------------------------------------------------
-- 호스트:                          127.0.0.1
-- 서버 버전:                        10.2.8-MariaDB - mariadb.org binary distribution
-- 서버 OS:                        Win64
-- HeidiSQL 버전:                  9.4.0.5125
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- hp2p 데이터베이스 구조 내보내기
CREATE DATABASE IF NOT EXISTS `hp2p` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci */;
USE `hp2p`;

-- 테이블 hp2p.hp2p_auth_peer 구조 내보내기
CREATE TABLE IF NOT EXISTS `hp2p_auth_peer` (
  `overlay_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `peer_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`overlay_id`,`peer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- 내보낼 데이터가 선택되어 있지 않습니다.
-- 테이블 hp2p.hp2p_overlay 구조 내보내기
CREATE TABLE IF NOT EXISTS `hp2p_overlay` (
  `overlay_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `title` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `overlay_type` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `sub_type` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `owner_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `expires` int(11) NOT NULL DEFAULT 0,
  `overlay_status` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `description` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `heartbeat_interval` int(11) NOT NULL DEFAULT 0,
  `heartbeat_timeout` int(11) NOT NULL DEFAULT 0,
  `auth_keyword` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `auth_type` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `auth_admin_key` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `auth_access_key` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`overlay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- 내보낼 데이터가 선택되어 있지 않습니다.
-- 테이블 hp2p.hp2p_peer 구조 내보내기
CREATE TABLE IF NOT EXISTS `hp2p_peer` (
  `peer_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `overlay_id` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `ticket_id` int(11) DEFAULT NULL,
  `overlay_type` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `sub_type` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `expires` int(11) DEFAULT NULL,
  `address` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `auth_password` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `num_primary` int(11) NOT NULL DEFAULT 0,
  `num_out_candidate` int(11) NOT NULL DEFAULT 0,
  `num_in_candidate` int(11) NOT NULL DEFAULT 0,
  `costmap` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `report_time` datetime DEFAULT NULL,
  PRIMARY KEY (`peer_id`,`overlay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- 내보낼 데이터가 선택되어 있지 않습니다.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
