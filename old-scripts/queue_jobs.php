<?php
require_once 'vendor/autoload.php';

$conf = (object) array(
	'db' => BIM_Config::db(),
	'queue' => BIM_Config::gearman(),
);

//require_once 'BIM/Jobs/Gearman.php';
$jobs = new BIM_Jobs_Gearman( $conf );
$jobs->queueJobs();

