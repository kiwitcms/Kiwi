-- MySQL dump 10.13  Distrib 5.5.28, for Linux (x86_64)
--
-- Host: localhost    Database: testopia_open_test
-- ------------------------------------------------------
-- Server version	5.5.28

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'Tester'),(2,'Administrator'),(3,'default'),(4,'System Admin');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `permission_id_refs_id_a7792de1` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
INSERT INTO `auth_message` VALUES (1,2,'The user \"root\" was deleted successfully.');
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=227 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can add group',2,'add_group'),(5,'Can change group',2,'change_group'),(6,'Can delete group',2,'delete_group'),(7,'Can add user',3,'add_user'),(8,'Can change user',3,'change_user'),(9,'Can delete user',3,'delete_user'),(10,'Can add message',4,'add_message'),(11,'Can change message',4,'change_message'),(12,'Can delete message',4,'delete_message'),(13,'Can add content type',5,'add_contenttype'),(14,'Can change content type',5,'change_contenttype'),(15,'Can delete content type',5,'delete_contenttype'),(16,'Can add session',6,'add_session'),(17,'Can change session',6,'change_session'),(18,'Can delete session',6,'delete_session'),(19,'Can add site',51,'add_site'),(20,'Can change site',51,'change_site'),(21,'Can delete site',51,'delete_site'),(22,'Can add log entry',7,'add_logentry'),(23,'Can change log entry',7,'change_logentry'),(24,'Can delete log entry',7,'delete_logentry'),(25,'Can add comment',52,'add_comment'),(26,'Can change comment',52,'change_comment'),(27,'Can delete comment',52,'delete_comment'),(28,'Can moderate comments',52,'can_moderate'),(29,'Can add comment flag',53,'add_commentflag'),(30,'Can change comment flag',53,'change_commentflag'),(31,'Can delete comment flag',53,'delete_commentflag'),(32,'Can add xml rpc log',54,'add_xmlrpclog'),(33,'Can change xml rpc log',54,'change_xmlrpclog'),(34,'Can delete xml rpc log',54,'delete_xmlrpclog'),(35,'Can add profiles',8,'add_profiles'),(36,'Can change profiles',8,'change_profiles'),(37,'Can delete profiles',8,'delete_profiles'),(38,'Can add groups',9,'add_groups'),(39,'Can change groups',9,'change_groups'),(40,'Can delete groups',9,'delete_groups'),(41,'Can add user group map',10,'add_usergroupmap'),(42,'Can change user group map',10,'change_usergroupmap'),(43,'Can delete user group map',10,'delete_usergroupmap'),(44,'Can add classification',11,'add_classification'),(45,'Can change classification',11,'change_classification'),(46,'Can delete classification',11,'delete_classification'),(47,'Can add product',12,'add_product'),(48,'Can change product',12,'change_product'),(49,'Can delete product',12,'delete_product'),(50,'Can add priority',13,'add_priority'),(51,'Can change priority',13,'change_priority'),(52,'Can delete priority',13,'delete_priority'),(53,'Can add milestone',14,'add_milestone'),(54,'Can change milestone',14,'change_milestone'),(55,'Can delete milestone',14,'delete_milestone'),(56,'Can add component',15,'add_component'),(57,'Can change component',15,'change_component'),(58,'Can delete component',15,'delete_component'),(59,'Can add version',16,'add_version'),(60,'Can change version',16,'change_version'),(61,'Can delete version',16,'delete_version'),(62,'Can add test build',17,'add_testbuild'),(63,'Can change test build',17,'change_testbuild'),(64,'Can delete test build',17,'delete_testbuild'),(65,'Can add test environment',18,'add_testenvironment'),(66,'Can change test environment',18,'change_testenvironment'),(67,'Can delete test environment',18,'delete_testenvironment'),(68,'Can add test environment category',19,'add_testenvironmentcategory'),(69,'Can change test environment category',19,'change_testenvironmentcategory'),(70,'Can delete test environment category',19,'delete_testenvironmentcategory'),(71,'Can add test environment element',20,'add_testenvironmentelement'),(72,'Can change test environment element',20,'change_testenvironmentelement'),(73,'Can delete test environment element',20,'delete_testenvironmentelement'),(74,'Can add test environment property',21,'add_testenvironmentproperty'),(75,'Can change test environment property',21,'change_testenvironmentproperty'),(76,'Can delete test environment property',21,'delete_testenvironmentproperty'),(77,'Can add test environment map',22,'add_testenvironmentmap'),(78,'Can change test environment map',22,'change_testenvironmentmap'),(79,'Can delete test environment map',22,'delete_testenvironmentmap'),(80,'Can add test tag',23,'add_testtag'),(81,'Can change test tag',23,'change_testtag'),(82,'Can delete test tag',23,'delete_testtag'),(83,'Can add test attachment',24,'add_testattachment'),(84,'Can change test attachment',24,'change_testattachment'),(85,'Can delete test attachment',24,'delete_testattachment'),(86,'Can add test attachment data',25,'add_testattachmentdata'),(87,'Can change test attachment data',25,'change_testattachmentdata'),(88,'Can delete test attachment data',25,'delete_testattachmentdata'),(89,'Can add tcms env group',26,'add_tcmsenvgroup'),(90,'Can change tcms env group',26,'change_tcmsenvgroup'),(91,'Can delete tcms env group',26,'delete_tcmsenvgroup'),(92,'Can add tcms env plan map',27,'add_tcmsenvplanmap'),(93,'Can change tcms env plan map',27,'change_tcmsenvplanmap'),(94,'Can delete tcms env plan map',27,'delete_tcmsenvplanmap'),(95,'Can add tcms env property',28,'add_tcmsenvproperty'),(96,'Can change tcms env property',28,'change_tcmsenvproperty'),(97,'Can delete tcms env property',28,'delete_tcmsenvproperty'),(98,'Can add tcms env group property map',29,'add_tcmsenvgrouppropertymap'),(99,'Can change tcms env group property map',29,'change_tcmsenvgrouppropertymap'),(100,'Can delete tcms env group property map',29,'delete_tcmsenvgrouppropertymap'),(101,'Can add tcms env value',30,'add_tcmsenvvalue'),(102,'Can change tcms env value',30,'change_tcmsenvvalue'),(103,'Can delete tcms env value',30,'delete_tcmsenvvalue'),(214,'Can delete tcms env run value map',74,'delete_tcmsenvrunvaluemap'),(213,'Can change tcms env run value map',74,'change_tcmsenvrunvaluemap'),(212,'Can add tcms env run value map',74,'add_tcmsenvrunvaluemap'),(107,'Can add Test case status',55,'add_testcasestatus'),(108,'Can change Test case status',55,'change_testcasestatus'),(109,'Can delete Test case status',55,'delete_testcasestatus'),(110,'Can add test case category',34,'add_testcasecategory'),(111,'Can change test case category',34,'change_testcasecategory'),(112,'Can delete test case category',34,'delete_testcasecategory'),(113,'Can add test case',35,'add_testcase'),(114,'Can change test case',35,'change_testcase'),(115,'Can delete test case',35,'delete_testcase'),(116,'Can add test case text',36,'add_testcasetext'),(117,'Can change test case text',36,'change_testcasetext'),(118,'Can delete test case text',36,'delete_testcasetext'),(119,'Can add test case plan',38,'add_testcaseplan'),(120,'Can change test case plan',38,'change_testcaseplan'),(121,'Can delete test case plan',38,'delete_testcaseplan'),(122,'Can add test case attachment',39,'add_testcaseattachment'),(123,'Can change test case attachment',39,'change_testcaseattachment'),(124,'Can delete test case attachment',39,'delete_testcaseattachment'),(125,'Can add test case component',40,'add_testcasecomponent'),(126,'Can change test case component',40,'change_testcasecomponent'),(127,'Can delete test case component',40,'delete_testcasecomponent'),(128,'Can add test case tag',41,'add_testcasetag'),(129,'Can change test case tag',41,'change_testcasetag'),(130,'Can delete test case tag',41,'delete_testcasetag'),(131,'Can add test case bug',56,'add_testcasebug'),(132,'Can change test case bug',56,'change_testcasebug'),(133,'Can delete test case bug',56,'delete_testcasebug'),(134,'Can add test plan type',42,'add_testplantype'),(135,'Can change test plan type',42,'change_testplantype'),(136,'Can delete test plan type',42,'delete_testplantype'),(137,'Can add test plan',43,'add_testplan'),(138,'Can change test plan',43,'change_testplan'),(139,'Can delete test plan',43,'delete_testplan'),(140,'Can add test plan text',44,'add_testplantext'),(141,'Can change test plan text',44,'change_testplantext'),(142,'Can delete test plan text',44,'delete_testplantext'),(143,'Can add test plan permission',45,'add_testplanpermission'),(144,'Can change test plan permission',45,'change_testplanpermission'),(145,'Can delete test plan permission',45,'delete_testplanpermission'),(146,'Can add test plan permissions regexp',46,'add_testplanpermissionsregexp'),(147,'Can change test plan permissions regexp',46,'change_testplanpermissionsregexp'),(148,'Can delete test plan permissions regexp',46,'delete_testplanpermissionsregexp'),(149,'Can add test plan attachment',47,'add_testplanattachment'),(150,'Can change test plan attachment',47,'change_testplanattachment'),(151,'Can delete test plan attachment',47,'delete_testplanattachment'),(152,'Can add test plan activity',48,'add_testplanactivity'),(153,'Can change test plan activity',48,'change_testplanactivity'),(154,'Can delete test plan activity',48,'delete_testplanactivity'),(155,'Can add test plan tag',49,'add_testplantag'),(156,'Can change test plan tag',49,'change_testplantag'),(157,'Can delete test plan tag',49,'delete_testplantag'),(158,'Can add test run',50,'add_testrun'),(159,'Can change test run',50,'change_testrun'),(160,'Can delete test run',50,'delete_testrun'),(161,'Can add test case run status',59,'add_testcaserunstatus'),(162,'Can change test case run status',59,'change_testcaserunstatus'),(163,'Can delete test case run status',59,'delete_testcaserunstatus'),(164,'Can add test case run',57,'add_testcaserun'),(165,'Can change test case run',57,'change_testcaserun'),(166,'Can delete test case run',57,'delete_testcaserun'),(167,'Can add test review',60,'add_testreview'),(168,'Can change test review',60,'change_testreview'),(169,'Can delete test review',60,'delete_testreview'),(170,'Can add test review case',58,'add_testreviewcase'),(171,'Can change test review case',58,'change_testreviewcase'),(172,'Can delete test review case',58,'delete_testreviewcase'),(173,'Can add tcms log model',61,'add_tcmslogmodel'),(174,'Can change tcms log model',61,'change_tcmslogmodel'),(175,'Can delete tcms log model',61,'delete_tcmslogmodel'),(176,'Can add test run tag',62,'add_testruntag'),(177,'Can change test run tag',62,'change_testruntag'),(178,'Can delete test run tag',62,'delete_testruntag'),(179,'Can add test run cc',63,'add_testruncc'),(180,'Can change test run cc',63,'change_testruncc'),(181,'Can delete test run cc',63,'delete_testruncc'),(182,'Can add tcms log model',64,'add_tcmslogmodel'),(183,'Can change tcms log model',64,'change_tcmslogmodel'),(184,'Can delete tcms log model',64,'delete_tcmslogmodel'),(185,'Can add bookmark category',65,'add_bookmarkcategory'),(186,'Can change bookmark category',65,'change_bookmarkcategory'),(187,'Can delete bookmark category',65,'delete_bookmarkcategory'),(188,'Can add bookmark',66,'add_bookmark'),(189,'Can change bookmark',66,'change_bookmark'),(190,'Can delete bookmark',66,'delete_bookmark'),(191,'Can add test case bug system',67,'add_testcasebugsystem'),(192,'Can change test case bug system',67,'change_testcasebugsystem'),(193,'Can delete test case bug system',67,'delete_testcasebugsystem'),(194,'Can add user activate key',68,'add_useractivatekey'),(195,'Can change user activate key',68,'change_useractivatekey'),(196,'Can delete user activate key',68,'delete_useractivatekey'),(197,'Can add profiles',69,'add_profiles'),(198,'Can change profiles',69,'change_profiles'),(199,'Can delete profiles',69,'delete_profiles'),(200,'Can add groups',70,'add_groups'),(201,'Can change groups',70,'change_groups'),(202,'Can delete groups',70,'delete_groups'),(203,'Can add user group map',71,'add_usergroupmap'),(204,'Can change user group map',71,'change_usergroupmap'),(205,'Can delete user group map',71,'delete_usergroupmap'),(206,'Can add bookmark category',72,'add_bookmarkcategory'),(207,'Can change bookmark category',72,'change_bookmarkcategory'),(208,'Can delete bookmark category',72,'delete_bookmarkcategory'),(209,'Can add bookmark',73,'add_bookmark'),(210,'Can change bookmark',73,'change_bookmark'),(211,'Can delete bookmark',73,'delete_bookmark'),(215,'Can add test plan component',75,'add_testplancomponent'),(216,'Can change test plan component',75,'change_testplancomponent'),(217,'Can delete test plan component',75,'delete_testplancomponent'),(218,'Can add user profile',76,'add_userprofile'),(219,'Can change user profile',76,'change_userprofile'),(220,'Can delete user profile',76,'delete_userprofile'),(221,'Can add test case email settings',77,'add_testcaseemailsettings'),(222,'Can change test case email settings',77,'change_testcaseemailsettings'),(223,'Can delete test case email settings',77,'delete_testcaseemailsettings'),(224,'Can add test plan email settings',78,'add_testplanemailsettings'),(225,'Can change test plan email settings',78,'change_testplanemailsettings'),(226,'Can delete test plan email settings',78,'delete_testplanemailsettings');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(75) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'admin','','','admin@example.com','sha1$96c96$d4d84261e94d0854842ecefbefae498848c6220d',1,1,1,'2013-12-09 10:49:52','2013-12-09 10:49:41');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `group_id_refs_id_f0ee9890` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `permission_id_refs_id_67e79cb` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `celery_taskmeta`
--

DROP TABLE IF EXISTS `celery_taskmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_taskmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(255) NOT NULL,
  `status` varchar(50) NOT NULL,
  `result` longtext,
  `date_done` datetime NOT NULL,
  `traceback` longtext,
  `hidden` tinyint(1) NOT NULL,
  `meta` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `celery_taskmeta_2ff6b945` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_tasksetmeta`
--

DROP TABLE IF EXISTS `celery_tasksetmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(255) NOT NULL,
  `result` longtext NOT NULL,
  `date_done` datetime NOT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`),
  KEY `celery_tasksetmeta_2ff6b945` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `classifications`
--

DROP TABLE IF EXISTS `classifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `classifications` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` mediumtext,
  `sortkey` smallint(6) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `classifications_name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classifications`
--

LOCK TABLES `classifications` WRITE;
/*!40000 ALTER TABLE `classifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `classifications` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `components`
--

DROP TABLE IF EXISTS `components`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `components` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `product_id` smallint(6) NOT NULL,
  `initialowner` mediumint(9) NOT NULL,
  `initialqacontact` mediumint(9) DEFAULT NULL,
  `description` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `components_product_id_idx` (`product_id`,`name`),
  KEY `components_name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `components`
--

LOCK TABLES `components` WRITE;
/*!40000 ALTER TABLE `components` DISABLE KEYS */;
/*!40000 ALTER TABLE `components` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_user_id` (`user_id`),
  KEY `django_admin_log_content_type_id` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2013-12-09 10:55:37',2,3,'1','root',3,'');
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_comment_flags`
--

DROP TABLE IF EXISTS `django_comment_flags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_comment_flags` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `comment_id` int(11) NOT NULL,
  `flag` varchar(30) NOT NULL,
  `flag_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`comment_id`,`flag`),
  KEY `comment_id_refs_id_373a05f7` (`comment_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_comment_flags`
--

LOCK TABLES `django_comment_flags` WRITE;
/*!40000 ALTER TABLE `django_comment_flags` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_comment_flags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_comments`
--

DROP TABLE IF EXISTS `django_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_comments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_pk` int(11) NOT NULL,
  `site_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `user_name` varchar(50) NOT NULL,
  `user_email` varchar(75) NOT NULL,
  `user_url` varchar(200) NOT NULL,
  `comment` longtext NOT NULL,
  `submit_date` datetime NOT NULL,
  `ip_address` char(15) DEFAULT NULL,
  `is_public` tinyint(1) NOT NULL,
  `is_removed` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `content_type_id_refs_id_f2a7975b` (`content_type_id`),
  KEY `user_id_refs_id_81622011` (`user_id`),
  KEY `idx_comments_site_contenttype_objpk` (`site_id`,`content_type_id`,`object_pk`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_comments`
--

LOCK TABLES `django_comments` WRITE;
/*!40000 ALTER TABLE `django_comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=79 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'permission','auth','permission'),(2,'group','auth','group'),(3,'user','auth','user'),(4,'message','auth','message'),(5,'content type','contenttypes','contenttype'),(6,'session','sessions','session'),(7,'log entry','admin','logentry'),(8,'profiles','accounts','profiles'),(9,'groups','accounts','groups'),(10,'user group map','accounts','usergroupmap'),(11,'classification','management','classification'),(12,'product','management','product'),(13,'priority','management','priority'),(14,'milestone','management','milestone'),(15,'component','management','component'),(16,'version','management','version'),(17,'test build','management','testbuild'),(18,'test environment','management','testenvironment'),(19,'test environment category','management','testenvironmentcategory'),(20,'test environment element','management','testenvironmentelement'),(21,'test environment property','management','testenvironmentproperty'),(22,'test environment map','management','testenvironmentmap'),(23,'test tag','management','testtag'),(24,'test attachment','management','testattachment'),(25,'test attachment data','management','testattachmentdata'),(26,'tcms env group','management','tcmsenvgroup'),(27,'tcms env plan map','management','tcmsenvplanmap'),(28,'tcms env property','management','tcmsenvproperty'),(29,'tcms env group property map','management','tcmsenvgrouppropertymap'),(30,'tcms env value','management','tcmsenvvalue'),(74,'tcms env run value map','testruns','tcmsenvrunvaluemap'),(59,'test case run status','testruns','testcaserunstatus'),(34,'test case category','testcases','testcasecategory'),(35,'test case','testcases','testcase'),(36,'test case text','testcases','testcasetext'),(60,'test review','testreviews','testreview'),(38,'test case plan','testcases','testcaseplan'),(39,'test case attachment','testcases','testcaseattachment'),(40,'test case component','testcases','testcasecomponent'),(41,'test case tag','testcases','testcasetag'),(42,'test plan type','testplans','testplantype'),(43,'test plan','testplans','testplan'),(44,'test plan text','testplans','testplantext'),(45,'test plan permission','testplans','testplanpermission'),(46,'test plan permissions regexp','testplans','testplanpermissionsregexp'),(47,'test plan attachment','testplans','testplanattachment'),(48,'test plan activity','testplans','testplanactivity'),(49,'test plan tag','testplans','testplantag'),(50,'test run','testruns','testrun'),(51,'site','sites','site'),(52,'comment','comments','comment'),(53,'comment flag','comments','commentflag'),(54,'xml rpc log','xmlrpc','xmlrpclog'),(55,'Test case status','testcases','testcasestatus'),(56,'test case bug','testcases','testcasebug'),(57,'test case run','testruns','testcaserun'),(58,'test review case','testreviews','testreviewcase'),(61,'tcms log model','core','tcmslogmodel'),(62,'test run tag','testruns','testruntag'),(63,'test run cc','testruns','testruncc'),(64,'tcms log model','logs','tcmslogmodel'),(65,'bookmark category','accounts','bookmarkcategory'),(66,'bookmark','accounts','bookmark'),(67,'test case bug system','testcases','testcasebugsystem'),(68,'user activate key','auth','useractivatekey'),(69,'profiles','profiles','profiles'),(70,'groups','profiles','groups'),(71,'user group map','profiles','usergroupmap'),(72,'bookmark category','profiles','bookmarkcategory'),(73,'bookmark','profiles','bookmark'),(75,'test plan component','testplans','testplancomponent'),(76,'user profile','profiles','userprofile'),(77,'test case email settings','testcases','testcaseemailsettings'),(78,'test plan email settings','testplans','testplanemailsettings');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'tcms.example.com','tcms.example.com');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_crontabschedule`
--

DROP TABLE IF EXISTS `djcelery_crontabschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_crontabschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `minute` varchar(64) NOT NULL,
  `hour` varchar(64) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  `day_of_month` varchar(64) NOT NULL,
  `month_of_year` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_intervalschedule`
--

DROP TABLE IF EXISTS `djcelery_intervalschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_intervalschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `every` int(11) NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_periodictask`
--

DROP TABLE IF EXISTS `djcelery_periodictask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `interval_id` int(11) DEFAULT NULL,
  `crontab_id` int(11) DEFAULT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `total_run_count` int(10) unsigned NOT NULL,
  `date_changed` datetime NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `djcelery_periodictask_8905f60d` (`interval_id`),
  KEY `djcelery_periodictask_7280124f` (`crontab_id`),
  CONSTRAINT `crontab_id_refs_id_286da0d1` FOREIGN KEY (`crontab_id`) REFERENCES `djcelery_crontabschedule` (`id`),
  CONSTRAINT `interval_id_refs_id_1829f358` FOREIGN KEY (`interval_id`) REFERENCES `djcelery_intervalschedule` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_periodictasks`
--

DROP TABLE IF EXISTS `djcelery_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictasks` (
  `ident` smallint(6) NOT NULL,
  `last_update` datetime NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_taskstate`
--

DROP TABLE IF EXISTS `djcelery_taskstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_taskstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state` varchar(64) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `tstamp` datetime NOT NULL,
  `args` longtext,
  `kwargs` longtext,
  `eta` datetime DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `result` longtext,
  `traceback` longtext,
  `runtime` double DEFAULT NULL,
  `retries` int(11) NOT NULL,
  `worker_id` int(11) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `djcelery_taskstate_5654bf12` (`state`),
  KEY `djcelery_taskstate_4da47e07` (`name`),
  KEY `djcelery_taskstate_abaacd02` (`tstamp`),
  KEY `djcelery_taskstate_cac6a03d` (`worker_id`),
  KEY `djcelery_taskstate_2ff6b945` (`hidden`),
  CONSTRAINT `worker_id_refs_id_6fd8ce95` FOREIGN KEY (`worker_id`) REFERENCES `djcelery_workerstate` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djcelery_workerstate`
--

DROP TABLE IF EXISTS `djcelery_workerstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_workerstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `last_heartbeat` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  KEY `djcelery_workerstate_11e400ef` (`last_heartbeat`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djkombu_message`
--

DROP TABLE IF EXISTS `djkombu_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djkombu_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `visible` tinyint(1) NOT NULL,
  `sent_at` datetime DEFAULT NULL,
  `payload` longtext NOT NULL,
  `queue_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `djkombu_message_5907bb86` (`visible`),
  KEY `djkombu_message_bc4c5ddc` (`sent_at`),
  KEY `djkombu_message_c80a9385` (`queue_id`),
  CONSTRAINT `queue_id_refs_id_88980102` FOREIGN KEY (`queue_id`) REFERENCES `djkombu_queue` (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `djkombu_queue`
--

DROP TABLE IF EXISTS `djkombu_queue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djkombu_queue` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `isbuggroup` tinyint(4) NOT NULL,
  `userregexp` tinytext NOT NULL,
  `isactive` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `groups_name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `groups`
--

LOCK TABLES `groups` WRITE;
/*!40000 ALTER TABLE `groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `keyworddefs`
--

DROP TABLE IF EXISTS `keyworddefs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `keyworddefs` (
  `id` smallint(6) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` mediumtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `keyworddefs_name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `keyworddefs`
--

LOCK TABLES `keyworddefs` WRITE;
/*!40000 ALTER TABLE `keyworddefs` DISABLE KEYS */;
/*!40000 ALTER TABLE `keyworddefs` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `milestones`
--

DROP TABLE IF EXISTS `milestones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `milestones` (
  `product_id` smallint(6) NOT NULL,
  `value` varchar(20) NOT NULL,
  `sortkey` smallint(6) NOT NULL DEFAULT '0',
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `milestones_product_id_idx` (`product_id`,`value`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `milestones`
--

LOCK TABLES `milestones` WRITE;
/*!40000 ALTER TABLE `milestones` DISABLE KEYS */;
/*!40000 ALTER TABLE `milestones` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `priority`
--

DROP TABLE IF EXISTS `priority`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `priority` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `value` varchar(64) NOT NULL,
  `sortkey` smallint(6) NOT NULL DEFAULT '0',
  `isactive` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `priority_value_idx` (`value`),
  KEY `priority_sortkey_idx` (`sortkey`,`value`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `priority`
--

LOCK TABLES `priority` WRITE;
/*!40000 ALTER TABLE `priority` DISABLE KEYS */;
/*!40000 ALTER TABLE `priority` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `products` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `classification_id` smallint(6) NOT NULL DEFAULT '1',
  `description` mediumtext,
  `milestoneurl` tinytext NOT NULL,
  `disallownew` tinyint(4) NOT NULL DEFAULT '0',
  `votesperuser` smallint(6) NOT NULL DEFAULT '0',
  `maxvotesperbug` smallint(6) NOT NULL DEFAULT '10000',
  `votestoconfirm` smallint(6) NOT NULL DEFAULT '0',
  `defaultmilestone` varchar(20) NOT NULL DEFAULT '---',
  PRIMARY KEY (`id`),
  UNIQUE KEY `products_name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `profiles`
--

DROP TABLE IF EXISTS `profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `profiles` (
  `userid` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `login_name` varchar(255) NOT NULL,
  `cryptpassword` varchar(128) DEFAULT NULL,
  `realname` varchar(255) NOT NULL DEFAULT '',
  `disabledtext` mediumtext NOT NULL,
  `mybugslink` tinyint(4) NOT NULL DEFAULT '1',
  `extern_id` varchar(64) DEFAULT NULL,
  `disable_mail` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`userid`),
  UNIQUE KEY `profiles_login_name_idx` (`login_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `profiles`
--

LOCK TABLES `profiles` WRITE;
/*!40000 ALTER TABLE `profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `profiles` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `tcms_bookmark_categories`
--

DROP TABLE IF EXISTS `tcms_bookmark_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_bookmark_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(1024) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_bookmark_categories_fbfc09f1` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_bookmark_categories`
--

LOCK TABLES `tcms_bookmark_categories` WRITE;
/*!40000 ALTER TABLE `tcms_bookmark_categories` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_bookmark_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_bookmarks`
--

DROP TABLE IF EXISTS `tcms_bookmarks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_bookmarks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) DEFAULT NULL,
  `object_pk` int(11),
  `site_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `category_id` int(11) DEFAULT NULL,
  `name` varchar(1024) NOT NULL,
  `description` longtext,
  `url` varchar(8192) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_bookmarks_e4470c6e` (`content_type_id`),
  KEY `tcms_bookmarks_6223029` (`site_id`),
  KEY `tcms_bookmarks_fbfc09f1` (`user_id`),
  KEY `tcms_bookmarks_42dc49bc` (`category_id`),
  KEY `tcms_bookmarks_62ffa694` (`content_type_id`, `object_pk`, `site_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_bookmarks`
--

LOCK TABLES `tcms_bookmarks` WRITE;
/*!40000 ALTER TABLE `tcms_bookmarks` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_bookmarks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_contacts`
--

DROP TABLE IF EXISTS `tcms_contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_contacts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) DEFAULT NULL,
  `object_pk` int(11),
  `site_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `email` varchar(75) NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `content_type_id_refs_id_ffc690d8` (`content_type_id`),
  KEY `site_id_refs_id_cd57d185` (`site_id`),
  KEY `tcms_contacts_62ffa694` (`content_type_id`, `object_pk`, `site_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_contacts`
--

LOCK TABLES `tcms_contacts` WRITE;
/*!40000 ALTER TABLE `tcms_contacts` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_contacts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_env_group_property_map`
--

DROP TABLE IF EXISTS `tcms_env_group_property_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_env_group_property_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `property_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_env_group_property_map_group_id` (`group_id`),
  KEY `tcms_env_group_property_map_property_id` (`property_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_env_group_property_map`
--

LOCK TABLES `tcms_env_group_property_map` WRITE;
/*!40000 ALTER TABLE `tcms_env_group_property_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_env_group_property_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_env_groups`
--

DROP TABLE IF EXISTS `tcms_env_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_env_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `manager_id` int(11) NOT NULL,
  `modified_by_id` int(11) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `tcms_env_groups_manager_id` (`manager_id`),
  KEY `tcms_env_groups_modified_by_id` (`modified_by_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_env_groups`
--

LOCK TABLES `tcms_env_groups` WRITE;
/*!40000 ALTER TABLE `tcms_env_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_env_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_env_plan_map`
--

DROP TABLE IF EXISTS `tcms_env_plan_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_env_plan_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_env_plan_map_plan_id` (`plan_id`),
  KEY `tcms_env_plan_map_group_id` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_env_plan_map`
--

LOCK TABLES `tcms_env_plan_map` WRITE;
/*!40000 ALTER TABLE `tcms_env_plan_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_env_plan_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_env_properties`
--

DROP TABLE IF EXISTS `tcms_env_properties`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_env_properties` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_env_properties`
--

LOCK TABLES `tcms_env_properties` WRITE;
/*!40000 ALTER TABLE `tcms_env_properties` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_env_properties` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_env_run_value_map`
--

DROP TABLE IF EXISTS `tcms_env_run_value_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_env_run_value_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `run_id` int(11) NOT NULL,
  `value_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_env_run_value_map_run_id` (`run_id`),
  KEY `tcms_env_run_value_map_value_id` (`value_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_env_run_value_map`
--

LOCK TABLES `tcms_env_run_value_map` WRITE;
/*!40000 ALTER TABLE `tcms_env_run_value_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_env_run_value_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_env_values`
--

DROP TABLE IF EXISTS `tcms_env_values`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_env_values` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `value` varchar(255) NOT NULL,
  `property_id` int(11) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `property_id` (`property_id`,`value`),
  KEY `tcms_env_values_property_id` (`property_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_env_values`
--

LOCK TABLES `tcms_env_values` WRITE;
/*!40000 ALTER TABLE `tcms_env_values` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_env_values` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_linkrefs`
--

DROP TABLE IF EXISTS `tcms_linkrefs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_linkrefs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) DEFAULT NULL,
  `object_pk` int(11),
  `site_id` int(11) NOT NULL,
  `name` varchar(64) NOT NULL,
  `url` longtext NOT NULL,
  `created_on` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_linkrefs_1bb8f392` (`content_type_id`),
  KEY `tcms_linkrefs_6223029` (`site_id`),
  KEY `tcms_linkrefs_62ffa694` (`object_pk`, `content_type_id`, `site_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_linkrefs`
--

LOCK TABLES `tcms_linkrefs` WRITE;
/*!40000 ALTER TABLE `tcms_linkrefs` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_linkrefs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_logs`
--

DROP TABLE IF EXISTS `tcms_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_pk` int(11) NOT NULL,
  `site_id` int(11) NOT NULL,
  `who_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `action` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_logs_content_type_id` (`content_type_id`),
  KEY `tcms_logs_site_id` (`site_id`),
  KEY `tcms_logs_who_id` (`who_id`),
  KEY `object_pk` (`object_pk`),
  KEY `tcms_logs_62ffa694` (`content_type_id`, `object_pk`, `site_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_logs`
--

LOCK TABLES `tcms_logs` WRITE;
/*!40000 ALTER TABLE `tcms_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_review_cases`
--

DROP TABLE IF EXISTS `tcms_review_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_review_cases` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `review_id` int(11) NOT NULL,
  `case_id` int(11) NOT NULL,
  `reviewer_id` int(11) DEFAULT NULL,
  `case_text_version` int(11) NOT NULL,
  `running_date` datetime NOT NULL,
  `close_date` datetime DEFAULT NULL,
  `is_current` tinyint(1) NOT NULL,
  `sort_key` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `review_id_refs_id_ba4bea5f` (`review_id`),
  KEY `case_id_refs_case_id_1ef737b6` (`case_id`),
  KEY `reviewer_id_refs_id_e9321e9b` (`reviewer_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_review_cases`
--

LOCK TABLES `tcms_review_cases` WRITE;
/*!40000 ALTER TABLE `tcms_review_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_review_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_reviews`
--

DROP TABLE IF EXISTS `tcms_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_reviews` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NOT NULL,
  `summary` varchar(255) NOT NULL,
  `notes` longtext,
  `author_id` int(11) NOT NULL,
  `build_id` int(11) NOT NULL,
  `start_date` datetime NOT NULL,
  `stop_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `plan_id_refs_plan_id_c18f7675` (`plan_id`),
  KEY `author_id_refs_id_ce2c30ff` (`author_id`),
  KEY `build_id_refs_build_id_4aacd99b` (`build_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_reviews`
--

LOCK TABLES `tcms_reviews` WRITE;
/*!40000 ALTER TABLE `tcms_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_reviews_default_reviewer`
--

DROP TABLE IF EXISTS `tcms_reviews_default_reviewer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_reviews_default_reviewer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testreview_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `testreview_id` (`testreview_id`,`user_id`),
  KEY `user_id_refs_id_f84ca972` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_reviews_default_reviewer`
--

LOCK TABLES `tcms_reviews_default_reviewer` WRITE;
/*!40000 ALTER TABLE `tcms_reviews_default_reviewer` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_reviews_default_reviewer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_reviews_env_value`
--

DROP TABLE IF EXISTS `tcms_reviews_env_value`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_reviews_env_value` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testreview_id` int(11) NOT NULL,
  `tcmsenvvalue_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `testreview_id` (`testreview_id`,`tcmsenvvalue_id`),
  KEY `tcmsenvvalue_id_refs_id_6ddc756d` (`tcmsenvvalue_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_reviews_env_value`
--

LOCK TABLES `tcms_reviews_env_value` WRITE;
/*!40000 ALTER TABLE `tcms_reviews_env_value` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_reviews_env_value` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_user_activate_keys`
--

DROP TABLE IF EXISTS `tcms_user_activate_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_user_activate_keys` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(40) DEFAULT NULL,
  `key_expires` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `tcms_user_activate_keys_user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_user_activate_keys`
--

LOCK TABLES `tcms_user_activate_keys` WRITE;
/*!40000 ALTER TABLE `tcms_user_activate_keys` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_user_activate_keys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tcms_user_profiles`
--

DROP TABLE IF EXISTS `tcms_user_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tcms_user_profiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `phone_number` varchar(128) NOT NULL,
  `url` varchar(200) NOT NULL,
  `im` varchar(128) NOT NULL,
  `im_type_id` int(11) DEFAULT NULL,
  `address` longtext NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tcms_user_profiles`
--

LOCK TABLES `tcms_user_profiles` WRITE;
/*!40000 ALTER TABLE `tcms_user_profiles` DISABLE KEYS */;
/*!40000 ALTER TABLE `tcms_user_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_attachment_data`
--

DROP TABLE IF EXISTS `test_attachment_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_attachment_data` (
  `attachment_id` int(11) NOT NULL,
  `contents` longblob,
  KEY `test_attachment_data_primary_idx` (`attachment_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_attachment_data`
--

LOCK TABLES `test_attachment_data` WRITE;
/*!40000 ALTER TABLE `test_attachment_data` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_attachment_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_attachments`
--

DROP TABLE IF EXISTS `test_attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_attachments` (
  `attachment_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `submitter_id` mediumint(9) NOT NULL,
  `description` mediumtext,
  `filename` mediumtext,
  `creation_ts` datetime NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `stored_name` mediumtext,
  PRIMARY KEY (`attachment_id`),
  KEY `test_attachments_submitter_idx` (`submitter_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_attachments`
--

LOCK TABLES `test_attachments` WRITE;
/*!40000 ALTER TABLE `test_attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_builds`
--

DROP TABLE IF EXISTS `test_builds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_builds` (
  `build_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` smallint(6) NOT NULL,
  `milestone` varchar(20) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `description` text,
  `isactive` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`build_id`),
  UNIQUE KEY `build_prod_idx` (`build_id`,`product_id`),
  UNIQUE KEY `build_product_id_name_idx` (`product_id`,`name`),
  KEY `build_name_idx` (`name`),
  KEY `build_milestone_idx` (`milestone`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_builds`
--

LOCK TABLES `test_builds` WRITE;
/*!40000 ALTER TABLE `test_builds` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_builds` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `test_case_attachments`
--

DROP TABLE IF EXISTS `test_case_attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_attachments` (
  `attachment_id` int(11) NOT NULL,
  `case_id` int(11) NOT NULL,
  `case_run_id` int(11) DEFAULT NULL,
  KEY `test_case_attachments_primary_idx` (`attachment_id`),
  KEY `attachment_case_id_idx` (`case_id`),
  KEY `attachment_caserun_id_idx` (`case_run_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_attachments`
--

LOCK TABLES `test_case_attachments` WRITE;
/*!40000 ALTER TABLE `test_case_attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_bug_systems`
--

DROP TABLE IF EXISTS `test_case_bug_systems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_bug_systems` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` longtext NOT NULL,
  `url_reg_exp` varchar(8192) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_bug_systems`
--

LOCK TABLES `test_case_bug_systems` WRITE;
/*!40000 ALTER TABLE `test_case_bug_systems` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_bug_systems` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_bugs`
--

DROP TABLE IF EXISTS `test_case_bugs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_bugs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bug_id` mediumint(9) NOT NULL,
  `case_run_id` int(11) DEFAULT NULL,
  `case_id` int(11) NOT NULL,
  `bug_system_id` int(11) NOT NULL,
  `summary` varchar(255) DEFAULT NULL,
  `description` mediumtext,
  PRIMARY KEY (`id`),
  KEY `case_bugs_bug_id_idx` (`bug_id`),
  KEY `case_bugs_case_id_idx` (`case_id`),
  KEY `case_bugs_case_run_id_idx` (`case_run_id`),
  KEY `case_bugs_case_bug_system_id_idx` (`bug_system_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_bugs`
--

LOCK TABLES `test_case_bugs` WRITE;
/*!40000 ALTER TABLE `test_case_bugs` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_bugs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_categories`
--

DROP TABLE IF EXISTS `test_case_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_categories` (
  `category_id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` smallint(6) NOT NULL,
  `name` varchar(240) NOT NULL,
  `description` mediumtext,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `category_product_id_name_idx` (`product_id`,`name`),
  UNIQUE KEY `category_product_idx` (`category_id`,`product_id`),
  KEY `category_name_idx_v2` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_categories`
--

LOCK TABLES `test_case_categories` WRITE;
/*!40000 ALTER TABLE `test_case_categories` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_components`
--

DROP TABLE IF EXISTS `test_case_components`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_components` (
  `case_id` int(11) NOT NULL,
  `component_id` smallint(5) unsigned NOT NULL,
  UNIQUE KEY `components_case_id_idx` (`case_id`,`component_id`),
  KEY `components_component_id_idx` (`component_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_components`
--

LOCK TABLES `test_case_components` WRITE;
/*!40000 ALTER TABLE `test_case_components` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_components` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `test_case_plans`
--

DROP TABLE IF EXISTS `test_case_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_plans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NOT NULL,
  `case_id` int(11) NOT NULL,
  `sortkey` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `test_case_plans_primary_idx` (`plan_id`,`case_id`),
  KEY `test_case_plans_case_idx` (`case_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_plans`
--

LOCK TABLES `test_case_plans` WRITE;
/*!40000 ALTER TABLE `test_case_plans` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_plans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_run_status`
--

DROP TABLE IF EXISTS `test_case_run_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_run_status` (
  `case_run_status_id` smallint(6) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) DEFAULT NULL,
  `sortkey` int(11) DEFAULT NULL,
  `description` mediumtext,
  `auto_blinddown` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`case_run_status_id`),
  UNIQUE KEY `uniq_idx_case_run_status_name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_run_status`
--

LOCK TABLES `test_case_run_status` WRITE;
/*!40000 ALTER TABLE `test_case_run_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_run_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_runs`
--

DROP TABLE IF EXISTS `test_case_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_runs` (
  `case_run_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` int(11) NOT NULL,
  `case_id` int(11) NOT NULL,
  `assignee_id` mediumint(9) DEFAULT NULL,
  `tested_by_id` mediumint(9) DEFAULT NULL,
  `case_run_status_id` tinyint(4) NOT NULL,
  `case_text_version` mediumint(9) NOT NULL,
  `build_id` int(11) NOT NULL,
  `close_date` datetime DEFAULT NULL,
  `notes` text,
  `iscurrent` tinyint(4) NOT NULL DEFAULT '0',
  `sortkey` int(11) DEFAULT NULL,
  `environment_id` int(11) NOT NULL,
  `running_date` datetime DEFAULT NULL,
  PRIMARY KEY (`case_run_id`),
  UNIQUE KEY `case_run_build_env_idx` (`run_id`,`case_id`,`build_id`,`environment_id`),
  KEY `case_run_case_id_idx` (`case_id`),
  KEY `case_run_assignee_idx` (`assignee_id`),
  KEY `case_run_testedby_idx` (`tested_by_id`),
  KEY `case_run_close_date_idx` (`close_date`),
  KEY `case_run_build_idx_v2` (`build_id`),
  KEY `case_run_env_idx_v2` (`environment_id`),
  KEY `case_run_status_idx` (`case_run_status_id`),
  KEY `case_run_text_ver_idx` (`case_text_version`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_runs`
--

LOCK TABLES `test_case_runs` WRITE;
/*!40000 ALTER TABLE `test_case_runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_runs` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `case_run_status_trigger_insert` AFTER INSERT ON `test_case_runs` FOR EACH ROW BEGIN
        UPDATE test_runs SET case_run_status = (
            SELECT
                group_concat(concat(a.status, ':', a.count)) AS status_count
            FROM (
                SELECT 
                    case_run_status_id AS status,
                    count(*) AS count FROM test_case_runs
                WHERE
                    run_id = NEW.run_id
                GROUP BY case_run_status_id
                ORDER BY status
            ) AS a
        )
        WHERE run_id = NEW.run_id;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `case_run_status_trigger_update` AFTER UPDATE ON `test_case_runs` FOR EACH ROW BEGIN
        UPDATE test_runs SET case_run_status = (
            SELECT
                group_concat(concat(a.status, ':', a.count)) AS status_count
            FROM (
                SELECT 
                    case_run_status_id AS status,
                    count(*) AS count FROM test_case_runs
                WHERE
                    run_id = NEW.run_id
                GROUP BY case_run_status_id
                ORDER BY status
            ) AS a
        )
        WHERE run_id = NEW.run_id;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = '' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `case_run_status_trigger_delete` AFTER DELETE ON `test_case_runs` FOR EACH ROW BEGIN
        UPDATE test_runs SET case_run_status = (
            SELECT
                group_concat(concat(a.status, ':', a.count)) AS status_count
            FROM (
                SELECT 
                    case_run_status_id AS status,
                    count(*) AS count FROM test_case_runs
                WHERE
                    run_id = OLD.run_id
                GROUP BY case_run_status_id
                ORDER BY status
            ) AS a
        )
        WHERE run_id = OLD.run_id;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `test_case_status`
--

DROP TABLE IF EXISTS `test_case_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_status` (
  `case_status_id` smallint(6) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` mediumtext,
  PRIMARY KEY (`case_status_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_status`
--

LOCK TABLES `test_case_status` WRITE;
/*!40000 ALTER TABLE `test_case_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_tags`
--

DROP TABLE IF EXISTS `test_case_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_tags` (
  `tag_id` int(11) NOT NULL,
  `case_id` int(11) NOT NULL,
  `userid` mediumint(9) NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `case_tags_primary_idx` (`tag_id`,`case_id`,`userid`),
  UNIQUE KEY `case_tags_secondary_idx` (`tag_id`,`case_id`),
  KEY `case_tags_case_id_idx_v3` (`case_id`),
  KEY `case_tags_userid_idx` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_tags`
--

LOCK TABLES `test_case_tags` WRITE;
/*!40000 ALTER TABLE `test_case_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_case_texts`
--

DROP TABLE IF EXISTS `test_case_texts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_case_texts` (
  `case_id` int(11) NOT NULL,
  `case_text_version` mediumint(9) NOT NULL,
  `who` mediumint(9) NOT NULL,
  `creation_ts` datetime NOT NULL,
  `action` mediumtext,
  `effect` mediumtext,
  `setup` mediumtext,
  `breakdown` mediumtext,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `case_versions_idx` (`case_id`,`case_text_version`),
  KEY `case_versions_who_idx` (`who`),
  KEY `case_versions_creation_ts_idx` (`creation_ts`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_case_texts`
--

LOCK TABLES `test_case_texts` WRITE;
/*!40000 ALTER TABLE `test_case_texts` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_case_texts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_cases`
--

DROP TABLE IF EXISTS `test_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_cases` (
  `case_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `case_status_id` tinyint(4) NOT NULL,
  `category_id` smallint(6) NOT NULL,
  `priority_id` smallint(6) DEFAULT NULL,
  `author_id` mediumint(9) NOT NULL,
  `default_tester_id` mediumint(9) DEFAULT NULL,
  `reviewer_id` int(11) DEFAULT NULL,
  `creation_date` datetime NOT NULL,
  `isautomated` tinyint(4) NOT NULL DEFAULT '0',
  `is_automated_proposed` tinyint(4) NOT NULL DEFAULT '0',
  `script` mediumtext,
  `arguments` mediumtext,
  `summary` varchar(255) DEFAULT NULL,
  `requirement` varchar(255) DEFAULT NULL,
  `alias` varchar(255) DEFAULT NULL,
  `estimated_time` time DEFAULT NULL,
  `notes` mediumtext,
  `extra_link` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`case_id`),
  KEY `test_case_category_idx` (`category_id`),
  KEY `test_case_author_idx` (`author_id`),
  KEY `test_case_creation_date_idx` (`creation_date`),
  KEY `test_case_requirement_idx` (`requirement`),
  KEY `test_case_shortname_idx` (`alias`),
  KEY `test_case_status_idx` (`case_status_id`),
  KEY `test_case_tester_idx` (`default_tester_id`),
  FULLTEXT `test_case_script_idx` (`script`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_cases`
--

LOCK TABLES `test_cases` WRITE;
/*!40000 ALTER TABLE `test_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_cases` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `test_environment_category`
--

DROP TABLE IF EXISTS `test_environment_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_environment_category` (
  `env_category_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` smallint(6) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`env_category_id`),
  UNIQUE KEY `test_environment_category_key1` (`env_category_id`,`product_id`),
  UNIQUE KEY `test_environment_category_key2` (`product_id`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_environment_category`
--

LOCK TABLES `test_environment_category` WRITE;
/*!40000 ALTER TABLE `test_environment_category` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_environment_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_environment_element`
--

DROP TABLE IF EXISTS `test_environment_element`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_environment_element` (
  `element_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `env_category_id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `isprivate` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`element_id`),
  UNIQUE KEY `test_environment_element_key1` (`element_id`,`env_category_id`),
  UNIQUE KEY `test_environment_element_key2` (`env_category_id`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_environment_element`
--

LOCK TABLES `test_environment_element` WRITE;
/*!40000 ALTER TABLE `test_environment_element` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_environment_element` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_environment_map`
--

DROP TABLE IF EXISTS `test_environment_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_environment_map` (
  `environment_id` int(11) NOT NULL,
  `property_id` int(11) NOT NULL,
  `element_id` int(11) NOT NULL,
  `value_selected` tinytext,
  UNIQUE KEY `test_environment_map_key3` (`environment_id`,`element_id`,`property_id`),
  KEY `env_map_env_element_idx` (`environment_id`,`element_id`),
  KEY `env_map_property_idx` (`environment_id`,`property_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_environment_map`
--

LOCK TABLES `test_environment_map` WRITE;
/*!40000 ALTER TABLE `test_environment_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_environment_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_environment_property`
--

DROP TABLE IF EXISTS `test_environment_property`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_environment_property` (
  `property_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `element_id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `validexp` text,
  PRIMARY KEY (`property_id`),
  UNIQUE KEY `test_environment_property_key1` (`property_id`,`element_id`),
  UNIQUE KEY `test_environment_property_key2` (`element_id`,`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_environment_property`
--

LOCK TABLES `test_environment_property` WRITE;
/*!40000 ALTER TABLE `test_environment_property` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_environment_property` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_environments`
--

DROP TABLE IF EXISTS `test_environments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_environments` (
  `environment_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` smallint(6) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `isactive` tinyint(4) NOT NULL DEFAULT '1',
  PRIMARY KEY (`environment_id`),
  UNIQUE KEY `test_environments_key1` (`environment_id`,`product_id`),
  UNIQUE KEY `test_environments_key2` (`product_id`,`name`),
  KEY `environment_name_idx_v2` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_environments`
--

LOCK TABLES `test_environments` WRITE;
/*!40000 ALTER TABLE `test_environments` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_environments` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `test_plan_activity`
--

DROP TABLE IF EXISTS `test_plan_activity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_activity` (
  `plan_id` int(11) NOT NULL,
  `fieldid` smallint(6) NOT NULL,
  `who` mediumint(9) NOT NULL,
  `changed` datetime NOT NULL,
  `oldvalue` mediumtext,
  `newvalue` mediumtext,
  KEY `plan_activity_who_idx` (`who`),
  KEY `plan_activity_changed_idx` (`changed`),
  KEY `plan_activity_field_idx` (`fieldid`),
  KEY `plan_activity_primary_idx` (`plan_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_activity`
--

LOCK TABLES `test_plan_activity` WRITE;
/*!40000 ALTER TABLE `test_plan_activity` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_activity` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_attachments`
--

DROP TABLE IF EXISTS `test_plan_attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_attachments` (
  `attachment_id` int(11) NOT NULL,
  `plan_id` int(11) NOT NULL,
  KEY `test_plan_attachments_primary_idx` (`attachment_id`),
  KEY `attachment_plan_id_idx` (`plan_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_attachments`
--

LOCK TABLES `test_plan_attachments` WRITE;
/*!40000 ALTER TABLE `test_plan_attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_components`
--

DROP TABLE IF EXISTS `test_plan_components`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_components` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NOT NULL,
  `component_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `plan_id` (`plan_id`,`component_id`),
  KEY `test_plan_components_plan_id` (`plan_id`),
  KEY `test_plan_components_component_id` (`component_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_components`
--

LOCK TABLES `test_plan_components` WRITE;
/*!40000 ALTER TABLE `test_plan_components` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_components` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_permissions`
--

DROP TABLE IF EXISTS `test_plan_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_permissions` (
  `userid` mediumint(9) NOT NULL,
  `plan_id` int(11) NOT NULL,
  `permissions` tinyint(4) NOT NULL,
  `grant_type` tinyint(4) NOT NULL,
  UNIQUE KEY `testers_plan_user_idx` (`userid`,`plan_id`,`grant_type`),
  KEY `testers_plan_user_plan_idx` (`plan_id`),
  KEY `testers_plan_grant_idx` (`grant_type`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_permissions`
--

LOCK TABLES `test_plan_permissions` WRITE;
/*!40000 ALTER TABLE `test_plan_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_permissions_regexp`
--

DROP TABLE IF EXISTS `test_plan_permissions_regexp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_permissions_regexp` (
  `plan_id` int(11) NOT NULL,
  `user_regexp` text NOT NULL,
  `permissions` tinyint(4) NOT NULL,
  UNIQUE KEY `testers_plan_regexp_idx` (`plan_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_permissions_regexp`
--

LOCK TABLES `test_plan_permissions_regexp` WRITE;
/*!40000 ALTER TABLE `test_plan_permissions_regexp` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_permissions_regexp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_tags`
--

DROP TABLE IF EXISTS `test_plan_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_tags` (
  `tag_id` int(11) NOT NULL,
  `plan_id` int(11) NOT NULL,
  `userid` mediumint(9) NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `plan_tags_primary_idx` (`tag_id`,`plan_id`,`userid`),
  UNIQUE KEY `plan_tags_secondary_idx` (`tag_id`,`plan_id`),
  KEY `plan_tags_plan_id_idx` (`plan_id`),
  KEY `plan_tags_userid_idx` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_tags`
--

LOCK TABLES `test_plan_tags` WRITE;
/*!40000 ALTER TABLE `test_plan_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_texts`
--

DROP TABLE IF EXISTS `test_plan_texts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_texts` (
  `plan_id` int(11) NOT NULL,
  `plan_text_version` int(11) NOT NULL,
  `who` mediumint(9) NOT NULL,
  `creation_ts` datetime NOT NULL,
  `plan_text` mediumtext,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  KEY `test_plan_text_version_idx` (`plan_id`,`plan_text_version`),
  KEY `test_plan_text_who_idx` (`who`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_texts`
--

LOCK TABLES `test_plan_texts` WRITE;
/*!40000 ALTER TABLE `test_plan_texts` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_texts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plan_types`
--

DROP TABLE IF EXISTS `test_plan_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plan_types` (
  `type_id` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` mediumtext,
  PRIMARY KEY (`type_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plan_types`
--

LOCK TABLES `test_plan_types` WRITE;
/*!40000 ALTER TABLE `test_plan_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plan_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_plans`
--

DROP TABLE IF EXISTS `test_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_plans` (
  `plan_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `product_id` smallint(6) NOT NULL,
  `author_id` mediumint(9) NOT NULL,
  `type_id` tinyint(4) NOT NULL,
  `default_product_version` mediumtext NOT NULL,
  `name` varchar(255) NOT NULL,
  `creation_date` datetime NOT NULL,
  `isactive` tinyint(4) NOT NULL DEFAULT '1',
  `extra_link` varchar(1024) DEFAULT NULL,
  `parent_id` int(10) unsigned DEFAULT NULL,
  `owner_id` mediumint(9) DEFAULT NULL,
  `product_version_id` mediumint(9) DEFAULT NULL,
  PRIMARY KEY (`plan_id`),
  KEY `plan_product_plan_id_idx` (`product_id`,`plan_id`),
  KEY `plan_author_idx` (`author_id`),
  KEY `plan_type_idx` (`type_id`),
  KEY `plan_isactive_idx` (`isactive`),
  KEY `plan_name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_plans`
--

LOCK TABLES `test_plans` WRITE;
/*!40000 ALTER TABLE `test_plans` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_plans` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `test_run_cc`
--

DROP TABLE IF EXISTS `test_run_cc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_run_cc` (
  `run_id` int(11) NOT NULL,
  `who` mediumint(9) NOT NULL,
  UNIQUE KEY `test_run_cc_primary_idx` (`run_id`,`who`),
  KEY `test_run_cc_who_idx` (`who`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_run_cc`
--

LOCK TABLES `test_run_cc` WRITE;
/*!40000 ALTER TABLE `test_run_cc` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_run_cc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_run_tags`
--

DROP TABLE IF EXISTS `test_run_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_run_tags` (
  `tag_id` int(11) NOT NULL,
  `run_id` int(11) NOT NULL,
  `userid` mediumint(9) NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_tags_primary_idx` (`tag_id`,`run_id`,`userid`),
  UNIQUE KEY `run_tags_secondary_idx` (`tag_id`,`run_id`),
  KEY `run_tags_run_id_idx` (`run_id`),
  KEY `run_tags_userid_idx` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_run_tags`
--

LOCK TABLES `test_run_tags` WRITE;
/*!40000 ALTER TABLE `test_run_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_run_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_runs`
--

DROP TABLE IF EXISTS `test_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_runs` (
  `run_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NOT NULL,
  `environment_id` int(11) NOT NULL,
  `product_version` mediumtext,
  `build_id` int(11) NOT NULL,
  `plan_text_version` int(11) NOT NULL,
  `manager_id` mediumint(9) NOT NULL,
  `default_tester_id` mediumint(9) DEFAULT NULL,
  `start_date` datetime NOT NULL,
  `stop_date` datetime DEFAULT NULL,
  `summary` tinytext NOT NULL,
  `notes` mediumtext,
  `target_pass` tinyint(4) DEFAULT NULL,
  `target_completion` tinyint(4) DEFAULT NULL,
  `estimated_time` time DEFAULT '00:00:00',
  `case_run_status` varchar(100) DEFAULT '',
  `errata_id` mediumint(9) DEFAULT NULL,
  `auto_update_run_status` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`run_id`),
  KEY `test_run_plan_id_run_id_idx` (`plan_id`,`run_id`),
  KEY `test_run_manager_idx` (`manager_id`),
  KEY `test_run_start_date_idx` (`start_date`),
  KEY `test_run_stop_date_idx` (`stop_date`),
  KEY `test_run_build_idx` (`build_id`),
  KEY `test_run_env_idx` (`environment_id`),
  KEY `test_run_plan_ver_idx` (`plan_text_version`),
  KEY `test_run_tester_idx` (`default_tester_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_runs`
--

LOCK TABLES `test_runs` WRITE;
/*!40000 ALTER TABLE `test_runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_tags`
--

DROP TABLE IF EXISTS `test_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_tags` (
  `tag_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`tag_id`),
  KEY `test_tag_name_idx_v2` (`tag_name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_tags`
--

LOCK TABLES `test_tags` WRITE;
/*!40000 ALTER TABLE `test_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testcases_testcaseemailsettings`
--

DROP TABLE IF EXISTS `testcases_testcaseemailsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testcases_testcaseemailsettings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` int(11) NOT NULL,
  `notify_on_case_update` tinyint(1) NOT NULL,
  `notify_on_case_delete` tinyint(1) NOT NULL,
  `auto_to_case_author` tinyint(1) NOT NULL,
  `auto_to_case_tester` tinyint(1) NOT NULL,
  `auto_to_run_manager` tinyint(1) NOT NULL,
  `auto_to_run_tester` tinyint(1) NOT NULL,
  `auto_to_case_run_assignee` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `case_id` (`case_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testcases_testcaseemailsettings`
--

LOCK TABLES `testcases_testcaseemailsettings` WRITE;
/*!40000 ALTER TABLE `testcases_testcaseemailsettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `testcases_testcaseemailsettings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testplans_testplanemailsettings`
--

DROP TABLE IF EXISTS `testplans_testplanemailsettings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testplans_testplanemailsettings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` int(11) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `auto_to_plan_owner` tinyint(1) NOT NULL,
  `auto_to_plan_author` tinyint(1) NOT NULL,
  `auto_to_case_owner` tinyint(1) NOT NULL,
  `auto_to_case_default_tester` tinyint(1) NOT NULL,
  `notify_on_plan_update` tinyint(1) NOT NULL,
  `notify_on_plan_delete` tinyint(1) NOT NULL,
  `notify_on_case_update` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `plan_id` (`plan_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testplans_testplanemailsettings`
--

LOCK TABLES `testplans_testplanemailsettings` WRITE;
/*!40000 ALTER TABLE `testplans_testplanemailsettings` DISABLE KEYS */;
/*!40000 ALTER TABLE `testplans_testplanemailsettings` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `user_group_map`
--

DROP TABLE IF EXISTS `user_group_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_group_map` (
  `user_id` mediumint(9) NOT NULL,
  `group_id` mediumint(9) NOT NULL,
  `isbless` tinyint(4) NOT NULL DEFAULT '0',
  `grant_type` tinyint(4) NOT NULL DEFAULT '0',
  UNIQUE KEY `user_group_map_user_id_idx` (`user_id`,`group_id`,`grant_type`,`isbless`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_group_map`
--

LOCK TABLES `user_group_map` WRITE;
/*!40000 ALTER TABLE `user_group_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_group_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `versions`
--

DROP TABLE IF EXISTS `versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `versions` (
  `value` varchar(64) NOT NULL,
  `product_id` smallint(6) NOT NULL,
  `id` mediumint(9) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `versions_product_id_idx` (`product_id`,`value`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `versions`
--

LOCK TABLES `versions` WRITE;
/*!40000 ALTER TABLE `versions` DISABLE KEYS */;
/*!40000 ALTER TABLE `versions` ENABLE KEYS */;
UNLOCK TABLES;


--
-- Table structure for table `xmlrpc_xmlrpclog`
--

DROP TABLE IF EXISTS `xmlrpc_xmlrpclog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `xmlrpc_xmlrpclog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dt_inserted` datetime NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `method` varchar(255) NOT NULL,
  `args` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id_refs_id_317d1de3` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `xmlrpc_xmlrpclog`
--

LOCK TABLES `xmlrpc_xmlrpclog` WRITE;
/*!40000 ALTER TABLE `xmlrpc_xmlrpclog` DISABLE KEYS */;
/*!40000 ALTER TABLE `xmlrpc_xmlrpclog` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-12-09 10:57:45
