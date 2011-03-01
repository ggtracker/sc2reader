<?php
include '../sc2/phpsc2replay-1.40/mpqfile.php';
include '../sc2/phpsc2replay-1.40/sc2map.php';

$start = microtime(true);

for ($i = 0; $i < 4; $i++) {
  $handler = opendir("test_replays/build17811/");
  while ($file = readdir($handler)) {
    if ($file != "." && $file != ".." && $file != "info.txt") {
      print $file."\n";
      $mpqfile = new MPQFile("test_replays/build17811/".$file);
      $replay = $mpqfile->parseReplay();
    }
  }
}

$end = (microtime(true) - $start);
print $end."\n";

# Results 1.3.2011
# 22.587602853775

?>