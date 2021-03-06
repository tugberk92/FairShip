from __future__ import division
from __future__ import print_function
import ROOT,os,sys,getopt,math
import shipunit as u
import proton_bremsstrahlung


PDG = ROOT.TDatabasePDG.Instance()
protonFlux = 2e20
 
 def getCascadeRate(mumPdg,th,pz):
    p8=ROOT.TFile(os.environ["EOSSHIP"]+"/eos/experiment/ship/data/DarkPhoton/PBC-June-3/Cascade/Cascade_Geant4-Pythia8_Theta-Pz.root")
    if abs(mumPdg)==2212:
        try:
            pr      = p8.Get("tdpr").Interpolate(th,pz)
            return pr
        except: return 1
    if mumPdg==111:
        try:
            pi0     = p8.Get("tdpi").Interpolate(th,pz)
            return pi0
        except: return 1
    if mumPdg==221:    
        try:
            eta     = p8.Get("tdet").Interpolate(th,pz)
            return eta
        except: return 1
    if mumPdg==223:
        try:
            omega   = p8.Get("tdom").Interpolate(th,pz)
            return omega
        except: return 1
    if mumPdg==331:
        try:
            eta1    = p8.Get("tdep").Interpolate(th,pz)
            return eta1
        except: return 1
    else:
        print(" -- ERROR, unknown mother pdgId %d for the Cascade"%mumPdg)
        return 1

def isDP(pdg):
    if (pdg==9900015 or pdg==4900023): 
        return True
    return False

def pbremProdRateVDM(mass,epsilon,doprint=False,E=400.,ptmax=4.0,zmin=0.1,zmax=0.9):
    xswg = proton_bremsstrahlung.prodRate(E, mass, epsilon, ptmax, proton_bremsstrahlung.pMin(E,mass,zmin), proton_bremsstrahlung.pMax(E,mass,zmax))
    if doprint: print("Ep= %.8g, A' production rate per p.o.t: \t %.8g"%(E,xswg))
    rhoff = proton_bremsstrahlung.rhoFormFactor(mass)**2
    if doprint: print("A' rho form factor: \t %.8g"%rhoff)
    if doprint: print("A' rescaled production rate per p.o.t:\t %.8g"%(xswg*rhoff))
    return xswg*rhoff

def pbremProdRateDipole(mass,epsilon,doprint=False,E=400.,ptmax=4.0,zmin=0.1,zmax=0.9):
    xswg = proton_bremsstrahlung.prodRate(E, mass, epsilon, ptmax, proton_bremsstrahlung.pMin(E,mass,zmin), proton_bremsstrahlung.pMax(E,mass,zmax))
    if doprint: print("Ep= %.8g, A' production rate per p.o.t: \t %.8g"%(E,xswg))
    penalty = proton_bremsstrahlung.penaltyFactor(mass)
    if doprint: print("A' penalty factor: \t %.8g"%penalty)
    if doprint: print("A' rescaled production rate per p.o.t:\t %.8g"%(xswg*penalty))
    return xswg*penalty

#obtained with Pythia8: average number of meson expected per p.o.t from inclusive pp to X production, 100k events produced
def getAverageMesonRate(mumPdg):
    if (mumPdg==111): return 6.166
    if (mumPdg==221): return 0.7012
    if (mumPdg==223): return 0.8295
    if (mumPdg==331): return 0.07825
    print(" -- ERROR, unknown mother pdgId %d"%mumPdg)
    return 0

#from the PDG, decay to photon channels available for mixing with DP
def mesonBRtoPhoton(mumPdg,doprint=False):
    br = 1
    if (mumPdg==111): br = 0.9879900
    if (mumPdg==221): br = 0.3931181
    if (mumPdg==223): br = 0.0834941
    if (mumPdg==331): br = 0.0219297
    if (doprint==True): print("BR of %d meson to photons: %.8g"%(mumPdg,br))
    return br 

def brMesonToGammaDP(mass,epsilon,mumPdg,doprint=False):
    mMeson = PDG.GetParticle(mumPdg).Mass()
    if (doprint==True): print("Mass of mother %d meson is %3.3f"%(mumPdg,mMeson))
    if (mass<mMeson): br = 2*epsilon**2*pow((1-mass**2/mMeson**2),3)*mesonBRtoPhoton(mumPdg,doprint)
    else: br = 0
    if (doprint==True): print("Branching ratio of %d meson to DP is %.8g"%(mumPdg,br))
    return br

def brMesonToMesonDP(mass,epsilon,mumPdg,dauPdg,doprint=False):
    mMeson = PDG.GetParticle(mumPdg).Mass()
    mDaughterMeson = PDG.GetParticle(dauPdg).Mass()
    if (doprint==True): print("Mass of mother %d meson is %3.3f"%(mumPdg,mMeson))
    if (doprint==True): print("Mass of daughter %d meson is %3.3f"%(dauPdg,mDaughterMeson))
    if (mass<(mMeson-mDaughterMeson)):
        fac1 = pow(mMeson**2.-mDaughterMeson**2.,-3.)
        fac2 = pow((mass**2.-(mMeson+mDaughterMeson)**2.)*(mass**2.-(mMeson-mDaughterMeson)**2.),1.5)
        massfactor = fac1*fac2
        br = (epsilon**2.)*mesonBRtoPhoton(mumPdg,doprint)*massfactor
    else: br = 0
    if (doprint==True): print("Branching ratio of %d meson to DP is %.8g"%(mumPdg,br))
    return br

def brMesonToDP(mass,epsilon,mumPdg,doprint=False):
    if mumPdg==223: return brMesonToMesonDP(mass,epsilon,mumPdg,111,doprint)
    elif (mumPdg==111 or mumPdg==221): return brMesonToGammaDP(mass,epsilon,mumPdg,doprint)
    elif mumPdg==331: return brMesonToMesonDP(mass,epsilon,mumPdg,113,doprint),brMesonToGammaDP(mass,epsilon,mumPdg,doprint)
    else: 
        print("Warning! Unknown mother pdgId %d, not implemented. Setting br to 0."%mumPdg)
        return 1

def mesonProdRate(mass,epsilon,mumPdg,doprint=False):
    brM2DP=brMesonToDP(mass,epsilon,mumPdg,doprint)
    if mumPdg==331:
        avgMeson = getAverageMesonRate(mumPdg)*brM2DP[0] 
        avgMeson1 = getAverageMesonRate(mumPdg)*brM2DP[1]
        return avgMeson, avgMeson1
        #return avgMeson + avgMeson1
    if not mumPdg==331:
        avgMeson = getAverageMesonRate(mumPdg)*brM2DP
        return avgMeson

#from interpolation of Pythia XS, normalised to epsilon^2
def qcdprodRate(mass,epsilon,doprint=False):
    if (mass > 3.):
        xs = math.exp(-5.51532-0.830917*mass)
    elif (mass > 1.4):
        xs = math.exp(-2.05488-1.96804*mass)
    else:
        xs = 0.
    return xs*epsilon*epsilon/10.7

def getDPprodRate(mass, epsilon, prodMode, mumPdg, doprint=False, E=400., ptmax=4.0, zmin=0.1, zmax=0.9):
    if (prodMode=='pbrem'):
        return pbremProdRateVDM(mass,epsilon,doprint,E,ptmax,zmin,zmax)
    elif (prodMode=='pbrem1'):
        return pbremProdRateDipole(mass,epsilon,doprint,E,ptmax,zmin,zmax)
    elif (prodMode=='meson'):
        return mesonProdRate(mass,epsilon,mumPdg,doprint)
    elif (prodMode=='qcd'):
        return qcdprodRate(mass,epsilon,doprint)
    else:
        print("Unknown production mode! Choose among pbrem, meson or qcd.")
        return 1
