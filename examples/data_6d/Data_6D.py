#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use data generated by micromechanical simulations to train ML yield function.

Authors: Ronak Shoghi, Alexander Hartmaier
ICAMS/Ruhr University Bochum, Germany
September 2022
"""
import pylabfea as FE
import numpy as np
import matplotlib.pyplot as plt
import src.pylabfea.training as CTD
import math
from matplotlib.lines import Line2D
import matplotlib.lines as mlines

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))


# Import Data
db = FE.Data("Data_Base_Updated_Final_Rotated_Train.JSON", wh_data=True)
#db = FE.Data("Data_Base_UpdatedE-07.json", Work_Hardening=False)
mat_ref = FE.Material(name="reference")  # define reference material, J2 plasticity, linear w.h.
mat_ref.elasticity(E=db.mat_data['E_av'], nu=db.mat_data['nu_av'])
mat_ref.plasticity(sy=db.mat_data['sy_av'], khard=4.5e3)
mat_ref.calc_properties(verb=False, eps=0.03, sigeps=True)

# db.plot_yield_locus(db =db, mat_data= db.mat_data, active ='flow_stress')
print(f'Successfully imported data for {db.mat_data["Nlc"]} load cases')
mat_ml = FE.Material(db.mat_data['Name'], num=1)  # define material
mat_ml.from_data(db.mat_data)  # data-based definition of material

# Train SVC with data from all microstructures
mat_ml.train_SVC(C=10, gamma=0.4, Fe=0.7, Ce=0.9, Nseq=2, gridsearch=False, plot=False)
print(f'Training successful.\nNumber of support vectors: {len(mat_ml.svm_yf.support_vectors_)}')

# Testing
sig_tot, epl_tot, yf_ref = CTD.Create_Test_Sig(Json="Data_Base_Updated_Final_Rotated_Test.json")
yf_ml = mat_ml.calc_yf(sig_tot, epl_tot, pred=False)
Results = CTD.training_score(yf_ref, yf_ml)
print(Results)
#Plot Hardening levels over a meshed space
#Plot initial and final hardening level of trained ML yield function together with data points
ngrid = 100
xx, yy = np.meshgrid(np.linspace(-1, 1, ngrid), np.linspace(0, 2, ngrid))
yy *= mat_ml.scale_seq
xx *= np.pi
hh = np.c_[yy.ravel(), xx.ravel()]
Cart_hh = FE.sp_cart(hh)
zeros_array = np.zeros((ngrid*ngrid, 3))
Cart_hh_6D = np.hstack((Cart_hh, zeros_array))
grad_hh = mat_ml.calc_fgrad(Cart_hh_6D)
norm_6d = np.linalg.norm(grad_hh)
normalized_grad_hh = grad_hh / FE.eps_eq(grad_hh)[:, None]  # norm_6d
Z = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0, pred=False)  # value of yield fct for every grid point
Z2 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.005, pred=False)
Z3 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.01, pred=False)
Z4 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.015, pred=False)
Z5 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.02, pred=False)
Z6 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.025, pred=False)

colors_hex = ['#550000', '#990000', '#bb0000', '#cc3333', '#ee3333', '#ff5050']
fig = plt.figure(figsize=(4.2, 4.2))
ax = fig.add_subplot(111, projection='polar')
ax.grid(True)
line = mat_ml.plot_data(Z, ax, xx, yy, c=colors_hex[0])
line2 = mat_ml.plot_data(Z2, ax, xx, yy, c=colors_hex[1])
line3 = mat_ml.plot_data(Z3, ax, xx, yy, c=colors_hex[2])
line4 = mat_ml.plot_data(Z4, ax, xx, yy, c=colors_hex[3])
line5 = mat_ml.plot_data(Z5, ax, xx, yy, c=colors_hex[4])
line6 = mat_ml.plot_data(Z6, ax, xx, yy, c=colors_hex[5])
fig.savefig('Hardening_Levels.png', dpi=300)
handle1 = Line2D([], [], color=colors_hex[0], label='Equivalent Plastic Strain : 0 ')
handle2 = Line2D([], [], color=colors_hex[1], label='Equivalent Plastic Strain : 0.5% ')
handle3 = Line2D([], [], color=colors_hex[2], label='Equivalent Plastic Strain : 1% ')
handle4 = Line2D([], [], color=colors_hex[3], label='Equivalent Plastic Strain : 1.5% ')
handle5 = Line2D([], [], color=colors_hex[4], label='Equivalent Plastic Strain : 2% ')
handle6 = Line2D([], [], color=colors_hex[5], label='Equivalent Plastic Strain : 2.5% ')
fig_leg = plt.figure(figsize=(4, 4))
ax_leg = fig_leg.add_subplot(111)
ax_leg.axis('off')
ax_leg.legend(handles=[handle1, handle2, handle3, handle4, handle5, handle6], loc="center")
fig_leg.savefig('Legend.png', dpi=300)
plt.show()
#
# Plot initial yield locus in pi-plane with the average yield strength from data
Z = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0, pred=False)  # value of yield fct for every grid point
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(5.6, 4.5))
linet, = mat_ml.plot_data(Z, ax, xx, yy, c='black')
linet.set_linewidth(2.2)
lineu = ax.axhline(db.mat_data['sy_av'], color='#9A1414', lw=2)
legend_elements = [
    Line2D([0], [0], color='black', lw=2, label='ML'),
    Line2D([0], [0], color='#9A1414', lw=2, label='Data')
]
ax.set_xlabel(r'$\theta$ (rad)', fontsize=14)
ax.set_ylabel(r'$\sigma_{eq}$ (MPa)', fontsize=14)
ax.tick_params(axis='both', which='major', labelsize=12)
ax.legend(handles=legend_elements, loc='upper right', fontsize=12)
plt.tight_layout()
fig.savefig('Initial_Yield_Locus.png', dpi=300)
plt.show()

# Reconstruct Stress-Strain Curve
Keys = list(db.Data_Visualization.keys())
Key = "Us_A1B2C2D1E1F2_4092b_5e411_Tx_Rnd"  # random.choice(Keys) # Select Data from database randomly
print("Selected Key is: {}".format(Key))
Stresses = db.Data_Visualization[Key]["Stress"]
Eq_Stresses = db.Data_Visualization[Key]["Eq_Stress"]
Strains = db.Data_Visualization[Key]["Strain"]
Eq_Strains = list(db.Data_Visualization[Key]["Eq_Strain"])
Eq_Shifted_Strains = list(db.Data_Visualization[Key]["Eq_Shifted_Strain"])
Response = []
Strains_for_Response = []
Eq_Stress_Drawing = []
Eq_Strains_Drawing = []

for counter, Eq_Strain in enumerate(Eq_Strains):
    if math.isnan(Eq_Shifted_Strains[counter]):
        continue
    else:
        if Eq_Strains[counter] < 0.002 or Eq_Strains[counter] > 0.028:
            continue
        else:
            Z=mat_ml.calc_yf(sig = Stresses, epl = Strains[counter],
                             pred = False)  # value of yield function for every grid point
            for counter2, val in enumerate(Z):
                if val > 0:
                    Response.append(Eq_Stresses[counter2])
                    Strains_for_Response.append(Eq_Strains[counter])
                    break

for counter, Eq_Strain in enumerate(Eq_Strains):
    if Eq_Strains[counter] > 0.028:
        continue
    else:
        Eq_Stress_Drawing.append(Eq_Stresses[counter])
        Eq_Strains_Drawing.append(Eq_Strains[counter])

fig = plt.figure(figsize=(5.6, 4.7))

plt.scatter(Eq_Strains_Drawing, Eq_Stress_Drawing, label="Data", s=8, color='black')
plt.scatter(Strains_for_Response, Response, label="ML", s=8,  color='#c60000')
plt.axvline(x=0.002, color='black', linestyle='--', ymax=50.5/plt.ylim()[1])
text_x_position = 0.002 + 0.0005
text_y_position = 46
text_size = 12
plt.text(text_x_position, text_y_position, '0.2% Equivalent Plastic Strain',
         color='black', ha='left', fontsize=text_size)
plt.tick_params(axis='both', which='major', labelsize=12)
plt.xlabel(xlabel="Equivalent Plastic Strain", fontsize=14)
plt.ylabel(ylabel="Equivalent Stress (MPa)", fontsize=14)
legend_font_size = 12
legend = plt.legend(fontsize=legend_font_size)
legend.legendHandles[0]._sizes = [50]
legend.legendHandles[1]._sizes = [50]
plt.tight_layout()
fig.savefig('Reconstructed_Stress_Strain_Curve.png', dpi=300)
plt.show()

# Plot initial and final hardening level of trained ML yield function together with data points
# get stress data
peeq_dat = FE.eps_eq(db.mat_data['plastic_strain'])
# ind0 = np.nonzero(peeq_dat < 0.0002)[0]
ind0 =np.nonzero(np.logical_and(peeq_dat > 0.00018, peeq_dat < 0.00022))[0]
sig_d0 = FE.s_cyl(db.mat_data['flow_stress'][ind0, :], mat_ml)
ind1 = np.nonzero(np.logical_and(peeq_dat > 0.0248, peeq_dat < 0.0252))[0]
sig_d1 = FE.s_cyl(db.mat_data['flow_stress'][ind1, :], mat_ml)
# calculate ML flow stresses
ngrid = 100
xx, yy = np.meshgrid(np.linspace(-1, 1, ngrid), np.linspace(0, 2, ngrid))
yy *= mat_ml.scale_seq
xx *= np.pi
hh = np.c_[yy.ravel(), xx.ravel()]
Cart_hh = FE.sp_cart(hh)
zeros_array = np.zeros((10000, 3))
Cart_hh_6D = np.hstack((Cart_hh, zeros_array))
grad_hh = mat_ml.calc_fgrad(Cart_hh_6D)
#norm_6d = np.linalg.norm(grad_hh)
normalized_grad_hh = grad_hh / FE.eps_eq(grad_hh)[:, None]  # norm_6d
Z0 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.,
                   pred=False)  # value of yield function for every grid point
Z1 = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0.025,
                   pred=False)
fig = plt.figure(figsize=(4.2, 4.2))
ax = fig.add_subplot(111, projection='polar')
ax.grid(True)
line = mat_ml.plot_data(Z0, ax, xx, yy, c="#600000")
line = mat_ml.plot_data(Z1, ax, xx, yy, c="#ff5050")
plt.scatter(sig_d0[:, 1], sig_d0[:, 0], s=5, c="black")
plt.scatter(sig_d1[:, 1], sig_d1[:, 0], s=5, c="black")
fig.savefig('ML+ScatterData.png', dpi=300)
plt.show()
handle1 = mlines.Line2D([], [], color="#550000", label='Equivalent Plastic Strain : 0 ')
handle2 = mlines.Line2D([], [], color="#ff3333", label='Equivalent Plastic Strain : 2.5% ')
fig_leg = plt.figure(figsize=(4, 4))
ax_leg = fig_leg.add_subplot(111)
ax_leg.axis('off')
ax_leg.legend(handles=[handle1, handle2], loc="center")
fig_leg.savefig('Legend2.png', dpi=300)
plt.show()

# Plot initial Hardening level with scatter data points
Stress_Set = []
Strain_Set = []
for Key in list(db.Data_Visualization.keys()):
    Response_Stress = []
    Response_Strain = []
    Eq_Strains=list(db.Data_Visualization[Key]["Eq_Strain"])
    Stresses = db.Data_Visualization[Key]["Stress"]
    for counter, Eq_Strain in enumerate(Eq_Strains):
        if Eq_Strains[counter] < 0.0019 or Eq_Strains[counter] > 0.0021:
            continue
        else:
            Response_Strain.append(Eq_Strains[counter])
            Response_Stress.append(Stresses[counter])
    if len(Response_Strain) == 0:
        continue
    else:
        Stress_Set.append(Response_Stress[0])
        Strain_Set.append(Response_Strain[0])
Stress_Set = np.array(Stress_Set)
Stress_Set_Princ, Stress_Set_EV = FE.sprinc(Stress_Set)
Stress_Set_Cyl = FE.s_cyl(Stress_Set_Princ)
Seq_Cyl = []
theta_Cyl = []
for set in Stress_Set_Cyl:
    Seq_Cyl.append(set[0])
    theta_Cyl.append(set[1])
Seq_Cyl = np.array(Seq_Cyl)
theta_Cyl = np.array(theta_Cyl)
ngrid = 100
xx, yy = np.meshgrid(np.linspace(-1, 1, ngrid), np.linspace(0, 2, ngrid))
yy *= mat_ml.scale_seq
xx *= np.pi
hh = np.c_[yy.ravel(), xx.ravel()]
Cart_hh = FE.sp_cart(hh)
zeros_array = np.zeros((10000, 3))
Cart_hh_6D = np.hstack((Cart_hh, zeros_array))
grad_hh = mat_ml.calc_fgrad(Cart_hh_6D)
norm_6d = np.linalg.norm(grad_hh)
normalized_grad_hh = grad_hh / norm_6d
Z = mat_ml.calc_yf(sig=Cart_hh_6D, epl=normalized_grad_hh * 0, pred=False) # value of yield function for every grid point
fig = plt.figure(figsize=(4.2, 4.2))
ax = fig.add_subplot(111, projection='polar')
ax.grid(True)
line = mat_ml.plot_data(Z, ax, xx, yy, c = "black")
plt.scatter(theta_Cyl, Seq_Cyl, s= 6, c = "red")

fig.savefig('ML+ScatterData.png', dpi=300)
handle1 = mlines.Line2D([], [], color = "blue", label='Equivalent Plastic Strain : 0 ')
fig_leg = plt.figure(figsize=(4, 4))
ax_leg = fig_leg.add_subplot(111)
ax_leg.axis('off')
ax_leg.legend(handles=[handle1], loc="center")
plt.show()


#Analysis of level of smoothness of the ML yield function using the gradient of the yield function
colors = ['blue', 'green', 'red', 'purple']
labels = ['High gamma', 'Low gamma', 'Low C', 'High C']

hyperparameters_sets = [
    {'C': 4, 'gamma': 10},  # Very high gamma
    {'C': 4, 'gamma': 0.1},  # Very low gamma
    {'C': 1, 'gamma': 0.5},  # Very low C
    {'C': 100, 'gamma': 0.5},  # Very high C
]

support_vectors_counts = []
grad_magnitudes_list = []
diff_grad_magnitudes_list = []

# Train and evaluate for each hyperparameter set, calculate gradient magnitudes and changes in gradient magnitudes for the inital yield locus
for hyperparameters in hyperparameters_sets:
    mat_ml.train_SVC(C=hyperparameters['C'], gamma=hyperparameters['gamma'], Fe=0.7, Ce=0.9, Nseq=1, gridsearch=False, plot=False)
    num_support_vectors = len(mat_ml.svm_yf.support_vectors_)
    support_vectors_counts.append(num_support_vectors)
    fixed_yy=mat_ml.scale_seq
    ngrid = 1000
    xx = np.linspace(-np.pi, np.pi, ngrid)
    yy = np.full_like(xx, fixed_yy).reshape(-1, 1)
    hh = np.c_[yy, xx]
    Cart_hh = FE.sp_cart(hh)
    zeros_array = np.zeros((ngrid, 3))
    Cart_hh_6D = np.hstack((Cart_hh, zeros_array))
    grad_hh = mat_ml.calc_fgrad(Cart_hh_6D)
    grad_magnitudes = np.linalg.norm(grad_hh, axis=1)
    diff_grad_magnitudes = np.diff(grad_magnitudes)
    grad_magnitudes_list.append(grad_magnitudes)
    diff_grad_magnitudes_list.append(diff_grad_magnitudes)

for i, hyperparameters in enumerate(hyperparameters_sets):
    print(f"For {labels[i]} (C={hyperparameters['C']}, gamma={hyperparameters['gamma']}): {support_vectors_counts[i]} support vectors")
overall_mean = np.mean(np.concatenate(grad_magnitudes_list))
std_devs = [np.std(gm) for gm in grad_magnitudes_list]


for i, s in enumerate(std_devs):
    print(f"Standard Deviation for {labels[i]}: {s:.4f}")

fig1, ax1 = plt.subplots(figsize=(8, 6))
y_min = np.min([np.min(gm) for gm in grad_magnitudes_list])
y_max = np.max([np.max(gm) for gm in grad_magnitudes_list])

for i, grad_magnitudes in enumerate(grad_magnitudes_list):
    mean_val = np.mean(grad_magnitudes)
    std_dev = np.std(grad_magnitudes)
    label_text = f"Support Vectors: {support_vectors_counts[i]}"
    ax1.plot(grad_magnitudes, color=colors[i], label=label_text, linewidth=2.0)
    ax1.axhline(mean_val, color=colors[i], linestyle='--', linewidth=1.5)

ax1.set_xlim(0, 1000)
ax1.set_ylim(y_min, y_max)
ax1.set_xlabel("Grid Points", fontsize=14)
ax1.set_ylabel("Gradient Magnitude", fontsize=14)
ax1.legend(fontsize=14, loc='upper center', bbox_to_anchor=(0.5, 1.15))  # Move legend to the top
ax1.tick_params(labelsize=14)
plt.tight_layout()
plt.show()

# Second figure for Changes in Gradient Magnitudes
fig2, ax2 = plt.subplots(figsize=(10, 8))
for i, diff_grad_magnitudes in enumerate(diff_grad_magnitudes_list):
    label_text = f"Support Vectors: {support_vectors_counts[i]}"
    ax2.plot(diff_grad_magnitudes, color=colors[i], label=label_text, linewidth=2.0)

ax2.axhline(0, color='black', linestyle='--', linewidth=2.0)
ax2.set_xlim(0, 1000)
ax2.set_xlabel("Grid Points", fontsize=16)
ax2.set_ylabel("Change in Gradient Magnitude", fontsize=16)
ax2.legend(fontsize=14)
ax2.tick_params(labelsize=14)
plt.tight_layout()
plt.show()


