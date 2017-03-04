# A new Get-RITA

Script for download data from BTS Airline On-Time Performance Data. Based heavily from the [isaccobezo's `get_rita`]
(https://github.com/isaacobezo/get_rita) repo.

Mainly we updated the code for using `Python 3`, and also the `data` that is send in the `POST`. In particular the field `geo` 
is adding an hexadecimal character `%A0` at the end.
