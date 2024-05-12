# Changelog

## 0.7.0
- RFM69HW and HCW specific functions and power level setting added by @Makodan

## 0.6.0
- Added support for ATC mode (thanks @MxMarx)
- Reduced some hang (thanks @MxMarx)
- Extended registers retrieved to include High Power PA settings (thanks @tomtastic)

## 0.5.1
- Added support for radios without reset pins

## 0.5.0
- Added set_frequency_in_Hz and get_frequency_in_Hz

## 0.4.0
- Made the Radio class threadsafe, and added threadsafe methods for accessing packets
- Added testing for the threadsafe methods
- Added pylinting and made some cosmetic changes to get a good pylint score
- Added coverage testing via coveralls.io, and instructions for doing so

## 0.3.0
- Added support for sendListenModeBurst
- Made tests more configurable
- Removed Python 2 from tests since it's EOL
- Added instructions on how to build for PyPi
