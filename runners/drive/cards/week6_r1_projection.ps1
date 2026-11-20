param(
    [Parameter(Mandatory)][string]$Database,
    [Parameter(Mandatory)][ValidateSet('Roster','Items')][string]$Projection
)
# Only the approved numeric and site fields cross this pipe to the counted child.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$path=(Resolve-Path -LiteralPath $Database).Path
$builder=[System.Data.Odbc.OdbcConnectionStringBuilder]::new()
$builder.Driver='Microsoft Access Driver (*.mdb, *.accdb)'
$builder['DBQ']=$path
$builder['ReadOnly']='True'
$columns=@('COUN','CITY','SUBJ','EMOT')
if($Projection -eq 'Items'){ $columns+=@('INTS','EXPC','PLEA','CAUS') }
$connection=[System.Data.Odbc.OdbcConnection]::new($builder.ConnectionString)
$command=$connection.CreateCommand()
$command.CommandText='SELECT '+(($columns | ForEach-Object {'['+$_+']'}) -join ',')+' FROM [DATA] WHERE [EMOT] IN (3,4)'
try {
    $connection.Open()
    $reader=$command.ExecuteReader()
    try {
        $culture=[Globalization.CultureInfo]::InvariantCulture
        while($reader.Read()){
            $fields=for($i=0;$i -lt $columns.Count;$i++){
                if($reader.IsDBNull($i)){ '' } else {
                    $v=[Convert]::ToString($reader.GetValue($i),$culture)
                    if($v.IndexOfAny([char[]]"`t`r`n") -ge 0){throw 'Unexpected delimiter in a projected field'}
                    $v
                }
            }
            [Console]::Out.WriteLine(($fields -join "`t"))
        }
    } finally { $reader.Dispose() }
} finally { $command.Dispose(); $connection.Dispose() }
