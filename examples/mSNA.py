from SoapySDR import *  # SOAPY_SDR_* constants
from pyLMS7002Soapy import pyLMS7002Soapy as pyLMSS
# import time
# import numpy as np
from matplotlib.pyplot import *
import matplotlib.ticker as ticker
import pylab as plt

# The above imports need to be cleaned up

# Checks the argument count for the cmdline applet
if len(sys.argv) != 5:
    print("Usage: python SNA.py measurementName fast(0|1) start end")
    exit(1)

measName = sys.argv[1]  # the file to save measurement
fastSweep = sys.argv[2]  # Sweeps fast(20MHz) or slow(5MHz)
startFreq = int(sys.argv[3]) * 1e06  # start frequency
endFreq = int(sys.argv[4]) * 1e06  # end frequency


class SNA(object):
    def __init__(self, sampleRate, cgenFreq, rfBandwidth, rfFreq, rxGain, txGain):
        self.sdr = pyLMSS.pyLMS7002Soapy(0)  # pyLMS7002 device instance
        self.sampleRate = sampleRate  # sample rate for limeSDR
        self.cgenFreq = cgenFreq  # center generator frequency
        self.rfBandwidth = rfBandwidth  # RF bandwidth
        self.rfFreq = rfFreq  # RF frequency
        self.rxGain = rxGain  # Rx Gain
        self.txGain = txGain  # Tx Gain
        self.sdr.configureAntenna(startFreq)

    def configRadio(self):  # Configures limeSDR & Returns RxStream
        self.sdr.rxSampleRate = self.sampleRate
        self.sdr.cgenFreq = self.cgenFreq
        self.sdr.rxBandWidth = self.rfBandwidth
        self.sdr.rxRfFreq = self.rfFreq
        self.sdr.rxGain = self.rxGain

        self.sdr.txSampleRate = self.sampleRate
        self.sdr.txBandwidth = self.rfBandwidth
        self.sdr.txGain = self.txGain
        self.sdr.txRfFreq = self.rfFreq

        rxStream = self.sdr.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0])
        self.sdr.tddMode = True  # Both Rx and Tx use Tx PLL
        self.sdr.testSignalDC(0x3fff, 0x3fff)
        return rxStream

    def readSamples(self, rxStream, nSamples):
        buff = np.zeros(2 * nSamples, np.complex64)
        self.sdr.sdr.activateStream(rxStream, SOAPY_SDR_END_BURST, 0, 2 * nSamples)
        numElemsRequest = 2 * nSamples
        while numElemsRequest > 0:
            sr = self.sdr.sdr.readStream(rxStream, [buff], 2 * nSamples)
            numElemsRequest -= sr.ret
        self.sdr.sdr.deactivateStream(rxStream)
        return buff[nSamples:]

    def f2s(self, val, decPlaces):
        tmp = round(val * 10 ** decPlaces)
        tmp = tmp / 10 ** decPlaces
        formatString = "%." + str(decPlaces) + "f"
        return formatString % tmp

    def userConfirmation(self, msg):
        userReady = 'n'
        while userReady != 'y':
            userReady = input(msg + '. Type y to continue. ')


if fastSweep:
    sampleRate = 20e6
    rfBandwidth = 100e6
    cgenFreq = 80e6
else:
    sampleRate = 5e6
    rfBandwidth = 50e6
    cgenFreq = 40e6


limeSNA = SNA(sampleRate, cgenFreq, rfBandwidth, startFreq, 20, 30)
rxStream = limeSNA.configRadio()

nwindow = 127.0
nSamples = (8192 * 4)

dncofreq = 2 * sampleRate * nwindow / nSamples
ncosteps = int(sampleRate / dncofreq / 4)
ncofreq = -(ncosteps + 0.5) * dncofreq
limeSNA.txNCOFreq = ncofreq

span = endFreq - startFreq
nFreqs = 2 * span / sampleRate
freqList = startFreq - ncofreq + (span / (nFreqs - 1.0)) * np.arange(0, nFreqs)

measFreq = []
measPowerSHORT = []
measPowerDUT = []
txGainList = []

txGain = 0

limeSNA.userConfirmation("Connect SHORT")

start_time = time.time()
for j in range(0, len(freqList)):
    freq = freqList[j]
    limeSNA.sdr.txRfFreq = freq
    limeSNA.sdr.configureAntenna(freq)
    ncofreq = -1.5 * dncofreq
    limeSNA.readSamples(rxStream, nSamples)
    limeSNA.readSamples(rxStream, nSamples)
    print("Measuring " + limeSNA.f2s((freq - ncosteps * dncofreq) / 1e6, 3) + " - " + limeSNA.f2s((freq + ncosteps * dncofreq) / 1e6,
                                                                                  3) + " MHz", end=" ")
    limeSNA.sdr.txNCOFreq = ncofreq
    samplePosition = int(ncofreq / sampleRate * nSamples + nSamples / 2.0)

    while txGain < 64:
        limeSNA.sdr.txGain = txGain
        buff = limeSNA.readSamples(rxStream, nSamples)
        spect = np.fft.fft(buff)
        spect = np.fft.fftshift(spect)
        power = 20 * np.log10(abs(spect[samplePosition]))
        if power < 65:
            txGain += 1
        elif power > 70:
            txGain -= 1
        else:
            break

    txGainList.append(txGain)
    limeSNA.sdr.txGain = txGain
    limeSNA.readSamples(rxStream, nSamples)

    for i in range(-ncosteps, ncosteps + 1):
        print(".", end="")
        ncofreq = (i + 0.5) * dncofreq
        limeSNA.sdr.txNCOFreq = ncofreq

        measFreq.append(freq + ncofreq)
        samplePosition = int(ncofreq / sampleRate * nSamples + nSamples / 2.0)
        buff = limeSNA.readSamples(rxStream, nSamples)

        spect = np.fft.fft(buff)
        spect = np.fft.fftshift(spect)
        measPowerSHORT.append(20 * np.log10(abs(spect[samplePosition])))
    print("")

measFreq = np.array(measFreq)
measPowerSHORT = np.array(measPowerSHORT)

limeSNA.userConfirmation("Connect DUT")

start_time = time.time()
for j in range(0, len(freqList)):
    freq = freqList[j]
    limeSNA.sdr.txRfFreq = freq
    limeSNA.sdr.configureAntenna(freq)
    ncofreq = -1.5 * dncofreq
    limeSNA.readSamples(rxStream, nSamples)
    limeSNA.readSamples(rxStream, nSamples)
    print("Measuring " + limeSNA.f2s((freq - ncosteps * dncofreq) / 1e6, 3) + " - " + limeSNA.f2s((freq + ncosteps * dncofreq) / 1e6,
                                                                                  3) + " MHz", end=" ")
    limeSNA.sdr.txNCOFreq = ncofreq
    samplePosition = int(ncofreq / sampleRate * nSamples + nSamples / 2.0)

    txGain = txGainList[j]
    limeSNA.sdr.txGain = txGain
    limeSNA.readSamples(rxStream, nSamples)

    for i in range(-ncosteps, ncosteps + 1):
        print(".", end="")
        ncofreq = (i + 0.5) * dncofreq
        limeSNA.sdr.txNCOFreq = ncofreq

        samplePosition = int(ncofreq / sampleRate * nSamples + nSamples / 2.0)
        buff = limeSNA.readSamples(rxStream, nSamples)

        spect = np.fft.fft(buff)
        spect = np.fft.fftshift(spect)
        measPowerDUT.append(20 * np.log10(abs(spect[samplePosition])))
    print("")

measPowerDUT = np.array(measPowerDUT)

s11 = measPowerDUT - measPowerSHORT

outFileName = measName + '.s1p'
outFile = open(outFileName, 'w')
outFile.write('# Hz S DB R 50\n')
for i in range(0, len(measFreq)):
    outFile.write(str(measFreq[i]) + "\t" + str(s11[i]) + "\t0\n")
outFile.close()

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(measFreq, s11)
xlabel("Frequency [MHz]")
scale_x = 1e06
ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
ax.xaxis.set_major_formatter(ticks_x)
ylabel("S11 [dB]")
plt.show()
