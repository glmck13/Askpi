#!/bin/ksh

PATH=$PWD:$PATH

NEXTWAV=.nextwav.conf DATAFILE=assist.dat

nextwav=$(<$NEXTWAV); (( nextwav = ++nextwav % 25 )); print $nextwav >$NEXTWAV

TMPWAV=./tmp/audio$nextwav.wav; rm -f $TMPWAV
. credentials.conf

typeset -l Speech LastWord Announce

[ "$REQUEST_METHOD" = "POST" ] && read -r QUERY_STRING

vars="$QUERY_STRING"
[ "$HTTP_COOKIE" ] && vars="${vars}&${HTTP_COOKIE}"
while [ "$vars" ]
do
	print $vars | IFS='&' read v vars
	[ "$v" ] && export $v
done

LastWord=$(urlencode -d "$LastWord") lastword="nil"
Speech=$(urlencode -d "$Speech")
Response=""
Html=""
Match="n"

if [ "$Speech" ]; then

	while read line
	do
		Token=${line:0:1} Pattern=${line#?}

		if [ "$Token" = "#" ]; then
			;

		elif [ "$Token" = "=" ]; then
			expr "$Speech" : "$Pattern" >/dev/null && Match="y"

		elif [ "$Token" = "+" ]; then
			expr "$LastWord $Speech" : "$Pattern" >/dev/null && Match="y"

		elif [ "$Match" != "y" ]; then
			;

		elif [ "$Token" = "~" ]; then
			lastword=$(eval print \""$Pattern"\")

		elif [ "$Token" = "!" ]; then
			eval "$Pattern"

		elif [ "$Token" = "." ]; then
			break

		elif [ "$Token" = "'" ]; then
			Html+=$(eval print \""$Pattern"\")

		else
			Response+=" "
			Response+=$(eval print "$line")
		fi

	done <$DATAFILE
fi

Audio="$Response"
if [ ! "$Audio" ]; then
	Audio=$(print "$Html" | grep '<p>' | sed -e "s/<[^>]*>//g")
fi

if [ "$Announce" != "t" -a "$Audio" ]; then
#	pico2wave -l en-US -w $TMPWAV "<volume level='60'>$Audio"
	print "$Audio" | grep -o -E '[^\.]*.' | split -l5 --filter=aws-polly.sh >$TMPWAV
fi
[ "$Announce" = "y" -a -f $TMPWAV ] && aplay $TMPWAV 2>/dev/null

typeset -A AnnounceButton
AnnounceButton["y"]="" AnnounceButton["n"]=""
AnnounceButton[${Announce:-n}]="checked"

cat - <<EOF
Content-type: text/html
Cache-Control: no-cache, no-store, must-revalidate
Set-Cookie: LastWord=$(urlencode "$lastword")

<html>
<head>
<meta name="viewport" content="width=device-width">
<link rel="apple-touch-icon" href="duncan.ico">
</head>

<body>
<form action="$SCRIPT_NAME" method="post">
	Enter your message:
	<br><textarea rows=8 cols=40 name="Speech" /></textarea>
	<br>Announce:
	<input type="radio" name="Announce" value="y" ${AnnounceButton["y"]} />Y
	<input type="radio" name="Announce" value="n" ${AnnounceButton["n"]} />N
	<br><input type="submit" name="Command" value="Submit" />
</form>
EOF

[ -f $TMPWAV ] && cat - <<EOF

<audio controls>
<source src="${SCRIPT_NAME%$(basename $SCRIPT_NAME)}$TMPWAV" type="audio/wav">
</audio> 
EOF

[ "$Response" ] && cat - <<EOF
<p>$Response</p>
EOF

[ "$Html" ] && cat - <<EOF
$Html
EOF

cat - <<EOF

</body>
</html>
EOF
