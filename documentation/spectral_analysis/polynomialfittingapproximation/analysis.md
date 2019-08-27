Super, merci pour cette reponse Benjamin !
Ca permets deja de valider les parametres obtenus par le fitting et/ou de simuler la resolution obtenue sur le capteur suivant le reseau utilise.

Pour le coup en 1d, asin et tan sont en effet des fonction tres regulieres et proche de x=y vers 0, dont la serie de taylor converge tres vite, donc le modele polynomial est tres adapte.
Techniquement si on s'interesse a l'erreur d'approximation de la serie de taylor en prenant une approximation de degree n=2, pour f(x) = 200*tan(asin(0.000015x))


Modulo l'offset sur le capteur j'imagine que la chose la plus compliquee a modeliser doit etre l'ensemble des defauts des optiques du spectroscope, qui sont j'imagine un peu plus complexe a obtenir de maniere analytique, et ont des composantes croisees xy en 2d.
