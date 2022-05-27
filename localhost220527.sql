-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- 생성 시간: 22-05-27 08:12
-- 서버 버전: 10.3.28-MariaDB
-- PHP 버전: 7.2.24

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 데이터베이스: `sensordb`
--
DROP DATABASE IF EXISTS `sensordb`;
CREATE DATABASE IF NOT EXISTS `sensordb` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `sensordb`;

-- --------------------------------------------------------

--
-- 테이블 구조 `accounts`
--

CREATE TABLE `accounts` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `fromip` varchar(20) DEFAULT NULL,
  `remark1` varchar(50) DEFAULT NULL,
  `regdate` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 테이블의 덤프 데이터 `accounts`
--

INSERT INTO `accounts` (`id`, `username`, `password`, `email`, `fromip`, `remark1`, `regdate`) VALUES
(2, 'test2', '$2b$12$H04WUPa8D68BSrz0kJ606ehLGUsgcUjvNGr2UVojboxZcbfE0NuMG', 'ylovepk67@gmail.com', '192.168.0.179', NULL, '2022-04-28 05:43:36'),
(3, 'test3', '$2b$12$9DTRCXgom8s21.uvRmYOPer2k2Eqx5ApM/R3fMOZaFx1hYzDqw2Ti', 'ylovepk@gmail.com', NULL, NULL, '2022-05-16 13:40:01');

-- --------------------------------------------------------

--
-- 테이블 구조 `cal_ro_tb`
--

CREATE TABLE `cal_ro_tb` (
  `Nos` int(10) NOT NULL,
  `SensorName` varchar(10) NOT NULL,
  `RO_Value` varchar(10) DEFAULT NULL,
  `checkdate` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 테이블의 덤프 데이터 `cal_ro_tb`
--

INSERT INTO `cal_ro_tb` (`Nos`, `SensorName`, `RO_Value`, `checkdate`) VALUES
(1, 'MQ135', '10.041', '2022-04-28 05:43:36'),
(2, 'MQ136', '09.786', '2022-04-28 05:43:36'),
(3, 'MQ137', '33.048', '2022-04-28 05:43:36'),
(4, 'MQ138', '33.048', '2022-04-28 05:43:36');

-- --------------------------------------------------------

--
-- 테이블 구조 `cal_scope_tb`
--

CREATE TABLE `cal_scope_tb` (
  `Nos` int(10) NOT NULL DEFAULT 0,
  `SensorName` varchar(10) NOT NULL,
  `level` int(1) DEFAULT NULL,
  `X_side` varchar(10) DEFAULT NULL,
  `Y_side` varchar(10) DEFAULT NULL,
  `Scope` varchar(10) DEFAULT NULL,
  `checkdate` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 테이블의 덤프 데이터 `cal_scope_tb`
--

INSERT INTO `cal_scope_tb` (`Nos`, `SensorName`, `level`, `X_side`, `Y_side`, `Scope`, `checkdate`) VALUES
(1, 'MQ135', 0, '+00.999', '-00.235', '-00.472', '2022-04-28 05:43:36'),
(2, 'MQ135', 1, '+02.000', '-00.707', '-00.515', '2022-04-28 05:43:36'),
(3, 'MQ135', 2, '+02.305', '-00.865', '-00.504', '2022-04-28 05:43:36'),
(4, 'MQ135', 3, '+02.703', '-01.065', '-00.475', '2022-04-28 05:43:36'),
(5, 'MQ136', 0, '+00.005', '-00.241', '-00.254', '2022-04-28 05:43:36'),
(6, 'MQ136', 1, '+01.013', '-00.497', '-00.269', '2022-04-28 05:43:36'),
(7, 'MQ136', 2, '+01.609', '-00.656', '-00.261', '2022-04-28 05:43:36'),
(8, 'MQ136', 3, '+01.976', '-00.754', '-00.272', '2022-04-28 05:43:36'),
(9, 'MQ137', 0, '+00.003', '-00.240', '-00.262', '2022-04-28 05:43:36'),
(10, 'MQ137', 1, '+00.991', '-00.499', '-00.259', '2022-04-28 05:43:36'),
(11, 'MQ137', 2, '+01.666', '-00.673', '-00.274', '2022-04-28 05:43:36'),
(12, 'MQ137', 3, '+02.022', '-00.771', '-00.263', '2022-04-28 05:43:36'),
(13, 'MQ138', 0, '+01.001', '-00.287', '-00.407', '2022-04-28 05:43:36'),
(14, 'MQ138', 1, '+01.689', '-00.567', '-00.538', '2022-04-28 05:43:36'),
(15, 'MQ138', 2, '+02.011', '-00.740', '-00.474', '2022-04-28 05:43:36'),
(16, 'MQ138', 3, '+02.287', '-00.871', '-00.421', '2022-04-28 05:43:36');

-- --------------------------------------------------------

--
-- 테이블 구조 `cmdprocess`
--

CREATE TABLE `cmdprocess` (
  `num` int(11) NOT NULL,
  `sensorid` varchar(1) NOT NULL,
  `cmd` varchar(2) NOT NULL,
  `tickets` varchar(10) NOT NULL,
  `s_flag` varchar(1) NOT NULL,
  `r_flag` varchar(1) DEFAULT NULL,
  `f_flag` varchar(1) DEFAULT NULL,
  `s_time` datetime NOT NULL,
  `r_time` datetime DEFAULT NULL,
  `f_time` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 테이블 구조 `sensoractiveconfig`
--

CREATE TABLE `sensoractiveconfig` (
  `sensorID` int(4) NOT NULL DEFAULT 0,
  `sensorName` varchar(50) NOT NULL,
  `runflage` tinyint(1) NOT NULL,
  `runcount` int(3) NOT NULL,
  `sdreadflage` tinyint(1) NOT NULL,
  `exhaustflage` tinyint(1) NOT NULL,
  `intakeflage` tinyint(1) NOT NULL,
  `resetflage` tinyint(1) NOT NULL,
  `runtimeflage` tinyint(1) NOT NULL,
  `roflage` tinyint(1) NOT NULL,
  `scopeflage` tinyint(1) NOT NULL,
  `sensorDate` datetime(6) NOT NULL DEFAULT current_timestamp(6) ON UPDATE current_timestamp(6),
  `remark` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 테이블의 덤프 데이터 `sensoractiveconfig`
--

INSERT INTO `sensoractiveconfig` (`sensorID`, `sensorName`, `runflage`, `runcount`, `sdreadflage`, `exhaustflage`, `intakeflage`, `resetflage`, `runtimeflage`, `roflage`, `scopeflage`, `sensorDate`, `remark`) VALUES
(0, '1차센서', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2022-05-23 13:13:34.382549', '1차센서'),
(1, '2차센서', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2022-05-23 13:13:34.382549', '2차센선'),
(2, '3차센서', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2022-05-23 13:13:34.382549', '3차센선'),
(3, '4차센서', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2022-05-23 13:13:34.382549', '4차센선'),
(4, '5차센서', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2022-05-23 13:13:34.382549', '5차센선');

-- --------------------------------------------------------

--
-- 테이블 구조 `sensordata`
--

CREATE TABLE `sensordata` (
  `chkCount` bigint(26) NOT NULL,
  `sensorID` int(11) NOT NULL,
  `H2` varchar(20) NOT NULL,
  `H2S` varchar(20) NOT NULL,
  `NH3` varchar(20) NOT NULL,
  `Toluene` varchar(20) NOT NULL,
  `CO2` varchar(20) NOT NULL,
  `VOC` varchar(20) NOT NULL,
  `CO` varchar(20) NOT NULL,
  `Temp1` varchar(10) NOT NULL,
  `Temp2` varchar(10) NOT NULL,
  `Hum1` varchar(10) NOT NULL,
  `Hum2` varchar(10) NOT NULL,
  `InputDateTime` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 테이블의 덤프 데이터 `sensordata`
--

INSERT INTO `sensordata` (`chkCount`, `sensorID`, `H2`, `H2S`, `NH3`, `Toluene`, `CO2`, `VOC`, `CO`, `Temp1`, `Temp2`, `Hum1`, `Hum2`, `InputDateTime`) VALUES
(1, 0, '  174.7860', '  198.2696', '   48.2727', '   67.1260', ' 7215.1284', ' 1569.2049', '   47.8410', '35', '25', '60', '55', '2022-04-29 00:17:24'),
(2, 1, '   54.8852', '   72.4319', '   91.0614', '   45.4329', ' 8336.3640', ' 5901.6929', '   32.7576', '27', '27', '65', '67', '2022-04-29 00:17:24'),
(3, 2, '   64.6141', '   22.1450', '  189.9281', '  145.6082', ' 7167.5641', ' 1830.9292', '   87.5547', '31', '31', '56', '65', '2022-04-29 00:17:24');

-- --------------------------------------------------------

--
-- 테이블 구조 `sensorlog`
--

CREATE TABLE `sensorlog` (
  `nos` bigint(20) NOT NULL,
  `commands` varchar(200) CHARACTER SET utf8 NOT NULL,
  `InputDateTime` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf16;

--
-- 테이블의 덤프 데이터 `sensorlog`
--

INSERT INTO `sensorlog` (`nos`, `commands`, `InputDateTime`) VALUES
(5320, 'login info: id:2, user:test2,client ip:172.30.1.33, logintime:2022-05-16 22:41:59', '2022-05-16 22:41:59'),
(5321, 'login info: id:2, user:test2,client ip:192.168.0.179, logintime:2022-05-19 17:30:21', '2022-05-19 17:30:21'),
(5322, 'login info: id:2, user:test2,client ip:192.168.0.179, logintime:2022-05-19 17:56:01', '2022-05-19 17:56:01');

-- --------------------------------------------------------

--
-- 테이블 구조 `sensorpumpruntime`
--

CREATE TABLE `sensorpumpruntime` (
  `sensorid` int(11) NOT NULL,
  `intaketimes` varchar(6) NOT NULL,
  `fittimes` varchar(6) NOT NULL,
  `exhausttimes` varchar(6) NOT NULL,
  `checkflage` tinyint(1) NOT NULL,
  `sensordate` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf32;

--
-- 테이블의 덤프 데이터 `sensorpumpruntime`
--

INSERT INTO `sensorpumpruntime` (`sensorid`, `intaketimes`, `fittimes`, `exhausttimes`, `checkflage`, `sensordate`) VALUES
(0, '780', '10', '30', 0, '2022-04-28 14:43:36'),
(1, '780', '10', '30', 0, '2022-04-28 14:43:36'),
(2, '780', '10', '30', 0, '2022-04-28 14:43:36'),
(3, '780', '10', '30', 0, '2022-04-28 14:43:36'),
(4, '780', '10', '30', 0, '2022-04-28 14:43:36');

-- --------------------------------------------------------

--
-- 테이블 구조 `sensortickets`
--

CREATE TABLE `sensortickets` (
  `num` int(11) NOT NULL,
  `sensorid` varchar(1) NOT NULL,
  `cmd` varchar(2) NOT NULL,
  `tickets` varchar(10) NOT NULL,
  `ack_send` varchar(10) NOT NULL,
  `s_flag` varchar(1) NOT NULL,
  `s_time` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 덤프된 테이블의 인덱스
--

--
-- 테이블의 인덱스 `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`id`);

--
-- 테이블의 인덱스 `cmdprocess`
--
ALTER TABLE `cmdprocess`
  ADD PRIMARY KEY (`num`);

--
-- 테이블의 인덱스 `sensordata`
--
ALTER TABLE `sensordata`
  ADD KEY `idx` (`chkCount`);

--
-- 테이블의 인덱스 `sensorlog`
--
ALTER TABLE `sensorlog`
  ADD PRIMARY KEY (`nos`);

--
-- 테이블의 인덱스 `sensorpumpruntime`
--
ALTER TABLE `sensorpumpruntime`
  ADD PRIMARY KEY (`sensorid`);

--
-- 테이블의 인덱스 `sensortickets`
--
ALTER TABLE `sensortickets`
  ADD PRIMARY KEY (`num`);

--
-- 덤프된 테이블의 AUTO_INCREMENT
--

--
-- 테이블의 AUTO_INCREMENT `accounts`
--
ALTER TABLE `accounts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- 테이블의 AUTO_INCREMENT `cmdprocess`
--
ALTER TABLE `cmdprocess`
  MODIFY `num` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- 테이블의 AUTO_INCREMENT `sensordata`
--
ALTER TABLE `sensordata`
  MODIFY `chkCount` bigint(26) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=306;

--
-- 테이블의 AUTO_INCREMENT `sensorlog`
--
ALTER TABLE `sensorlog`
  MODIFY `nos` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5323;

--
-- 테이블의 AUTO_INCREMENT `sensorpumpruntime`
--
ALTER TABLE `sensorpumpruntime`
  MODIFY `sensorid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- 테이블의 AUTO_INCREMENT `sensortickets`
--
ALTER TABLE `sensortickets`
  MODIFY `num` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
