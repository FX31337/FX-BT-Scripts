<?php
/*
   Script to download historical data from Dukascopy site.

  Usage:
    1. Before downloading define ourselves by what date the script can download the data, so enter the date that interests you.
       You can also fire up MT4 and throw the script data.mq4 on the chart.
       The communication we have given the correct date format that we use in the script (the date specified in the sample script below is - 1230768000.
       You can also use the Epoch Converter to change the format to format linux seconds-since-1970 format at epochconverter.com.

    2. Then, the resulting date format type in a file along with the selected currency pair. Here's an example:

    <? php
    $ currencies = array (
    牋牋 "USDJPY" => 1230768000
    牋牋 );

    then we save the file. If you don't create a file, then by default EURUSD would be downloaded.

    3. Finally run like this:

      php dl_bt_dukascopy.php

*/

/*
$currencies = array(
    "AUDJPY" => 1175270400, // starting from 2007.03.30 16:00
    "AUDNZD" => 1229961600, // starting from 2008.12.22 16:00
    "AUDUSD" => 1175270400, // starting from 2007.03.30 16:00
    "CADJPY" => 1175270400, // starting from 2007.03.30 16:00
    "CHFJPY" => 1175270400, // starting from 2007.03.30 16:00
    "EURAUD" => 1175270400, // starting from 2007.03.30 16:00
    "EURCAD" => 1222167600, // starting from 2008.09.23 11:00
    "EURCHF" => 1175270400, // starting from 2007.03.30 16:00
    "EURGBP" => 1175270400, // starting from 2007.03.30 16:00
    "EURJPY" => 1175270400, // starting from 2007.03.30 16:00
    "EURNOK" => 1175270400, // starting from 2007.03.30 16:00
    "EURSEK" => 1175270400, // starting from 2007.03.30 16:00
    "EURUSD" => 1175270400, // starting from 2007.03.30 16:00
    "GBPCHF" => 1175270400, // starting from 2007.03.30 16:00
    "GBPJPY" => 1175270400, // starting from 2007.03.30 16:00
    "GBPUSD" => 1175270400, // starting from 2007.03.30 16:00
    "NZDUSD" => 1175270400, // starting from 2007.03.30 16:00
    "USDCAD" => 1175270400, // starting from 2007.03.30 16:00
    "USDCHF" => 1175270400, // starting from 2007.03.30 16:00
    "USDJPY" => 1175270400, // starting from 2007.03.30 16:00
    "USDNOK" => 1222639200, // starting from 2008.09.28 22:00
    "USDSEK" => 1222642800, // starting from 2008.09.28 23:00
    "USDSGD" => 1222642800, // starting from 2008.09.28 23:00
    "AUDCAD" => 1266318000, // starting from 2010.02.16 11:00
    "AUDCHF" => 1266318000, // starting from 2010.02.16 11:00
    "CADCHF" => 1266318000, // starting from 2010.02.16 11:00
    "EURNZD" => 1266318000, // starting from 2010.02.16 11:00
    "GBPAUD" => 1266318000, // starting from 2010.02.16 11:00
    "GBPCAD" => 1266318000, // starting from 2010.02.16 11:00
    "GBPNZD" => 1266318000, // starting from 2010.02.16 11:00
    "NZDCAD" => 1266318000, // starting from 2010.02.16 11:00
    "NZDCHF" => 1266318000, // starting from 2010.02.16 11:00
    "NZDJPY" => 1266318000, // starting from 2010.02.16 11:00
    "XAGUSD" => 1289491200, // starting from 2010.11.11 16:00
    "XAUUSD" => 1305010800, // starting from 2011.05.10 07:00
    );
*/

if (file_exists('currencies.php')) {
  require 'currencies.php';
} else {
  $currencies = array (
    "EURUSD" => 1175270400, // starting from 2007.03.30 16:00
  );
}

$missingfilecount = 0;/*服务器上不存在的文件数量*/
$failedfilecount = 0;/*下载中途出错的文件数量*/
$successfilecount = 0;/*正常下载的文件数量*/
$skippedfilecount = 0;/*本地已经存在，被跳过的文件数量*/
$quitstring = "正常";

$lasttime = 0;/*每次下载某一天的第一个文件前记录当前GMT时间*/
$lastday = 0;/*下载前一天的Day数*/

/*获取并显示当前的GMT时间*/
$curtime = time();
error("Current GMT time:".gmstrftime("%m/%d/%Y %H:%M:%S",$curtime)."\r\n");

/*对每一个货币对进行循环下载，当前版本currencies.php仅仅包含一个货币对*/
foreach($currencies as $pair => $firsttick) {

    $firsttick -= $firsttick % 3600;
    error("Info: Downloading $pair starting with ".gmstrftime("%m/%d/%Y %H:%M:%S",$firsttick)."\r\n");

	/*逐次下载各个文件，每个文件包含一个小时的tick数据*/
    for($i = $firsttick; $i < $curtime-3600; $i += 3600) {
        $year = gmstrftime('%Y',$i);
        $month = str_pad(gmstrftime('%m',$i) - 1, 2, '0', STR_PAD_LEFT); /*格式化(month-1)，比如 1月份则转换为 00， 2月份-> 01 */
        $day = gmstrftime('%d',$i);
        $hour = gmstrftime('%H',$i);
        $url = "http://www.dukascopy.com/datafeed/$pair/$year/$month/$day/{$hour}h_ticks.bi5";

		/*当开始下载某一天的第一个文件前对$lasttim, $lastday做记录。作用其实就是提示下载到哪一天，无其他实际作用。*/
		if ($day != $lastday)
		{
			/*如果下载前一天的BIN数据在3秒内就被处理完毕，认为前一天的数据已经被下载*/
			if (time() - $lasttime < 3)
			{
				//error("BIN data already downloaded. Skipped.\r\n");
			}

			$lasttime = time();
			$lastday = $day;
			echo("Info: Downloading BIN data of $pair- ".gmstrftime("%m/%d/%Y",$i)."\r\n");
		}

		/*计算本地存储路径*/
        $localpath = "$pair/$year/$month/$day/";
        $binlocalfile = $localpath . $hour . "h_ticks.bin";
        $localfile = $localpath . $hour . "h_ticks.bi5";
        if (!file_exists($localpath)) {
            mkdir($localpath, 0777, true);
        }

		/*仅当本地文件不存在时候才启动下载*/
        if (!file_exists($localfile) && !file_exists($binlocalfile)) {
            $ch = FALSE;
            $j = 0;

			/*若无法连接服务器则连续尝试下载，最多尝试三次*/
            do {
                if ($ch !== FALSE) {
                    curl_close($ch);
                }
                $ch = curl_init($url);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($ch, CURLOPT_BINARYTRANSFER, true);
                curl_setopt($ch, CURLOPT_HEADER, 0);
                $result = curl_exec($ch);
                $j++;
            } while ($j <= 3 && curl_errno($ch));

			/*尝试三次仍然无法连接服务器则退出程序. */
            if (curl_errno($ch)) {
                error("FATAL: Couldn't download $url.\r\nError was: ".curl_error($ch)."\r\n");
				$quitstring = "无法连接服务器";
                exit(1);
            }
			/*服务器返回了数据，但是并不一定代表下载成功*/
            else {

				/*服务器返回404号码，表示想要下载的文件不存在*/
                if (curl_getinfo($ch, CURLINFO_HTTP_CODE) == 404) {
                    $weekday = gmstrftime('%a',$i);
                    if (strcasecmp($weekday,'sun') == 0 || strcasecmp($weekday,'sat') == 0) {
                        /*missing file是在周末数据*/
                        error("Info: missing weekend file $url\r\n");
                    }
                    else {
                        error("WARNING: missing file $url ($i - ".gmstrftime("%m/%d/%Y %H:%M GMT",$i).")\r\n");
                    }

					$missingfilecount++;
                }
				/*服务器返回200号码，表示文件被完整下载*/
                else if (curl_getinfo($ch, CURLINFO_HTTP_CODE) == 200) {
                    $outfd = fopen($localfile, 'wb');
                    if ($outfd === FALSE) {
                        error("FATAL: Couldn't open $localfile ($url - $i)\r\n");
						$quitstring = "创建本地文件出错";
                        exit(1);
                    }
                    fwrite($outfd, $result);
                    fclose($outfd);
                    //error("Info: successfully downloaded $url\r\n");
					$successfilecount++;
                }
				/*未知的返回号码，表示文件下载出未知错误*/
                else {
                    error("WARNING: did not download $url ($i - ".gmstrftime("%m/%d/%Y %H:%M GMT",$i).") - error code was ".curl_getinfo($ch, CURLINFO_HTTP_CODE)."\r\nContent was: $result\r\n");

					$failedfilecount++;
                }
            }
            curl_close($ch);
        }
        else {
			/*本地文件已经存在，直接跳过。程序的逻辑保证了下载的每个文件都是完整的。*/
            //error("Info: skipping $url, local file already exists.\r\n");
			$skippedfilecount++;
        }

		/*这里结束一个文件的下载，即将进入下一个文件*/

    }

	$totalseconds = time() - $curtime;

	error("已经完成".$pair."的下载任务。 共计使用". outtm($totalseconds)."。退出时的状态为:".$quitstring."。\r\n");
	error("共有".$successfilecount."个文件在本次任务中被下载。\r\n有".$skippedfilecount."个文件本地已经存在而被跳过。\r\n");
	error("有".$missingfilecount."个文件在服务器端缺失而未能下载。\r\n有".$failedfilecount."个文件在下载过程中出现未知错误而未能保存任何数据。\r\n");


	/*这里结束一个货币对所有文件的下载的下载，即将进入下一个货币对。当前版本我们仅仅处理一对货币对，故使用break跳出循环，实际结束程序*/
	break;
}



function error($error) {
    echo $error;
    $fd = fopen('error.log', 'a+');
    fwrite($fd, $error);
    fclose($fd);
}


/*
根据经过的秒数返回成 天：小时，分钟，秒的格式。
*/

function outtm($sec){
	$d = floor($sec / 86400);
	$tmp = $sec % 86400;
	$h = floor($tmp / 3600);
	$tmp %= 3600;
	$m = floor($tmp /60);
	$s = $tmp % 60;
	return "[".$d."天".$h."小时".$m."分".$s."秒]";
}
