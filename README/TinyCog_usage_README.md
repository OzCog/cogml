## TinyCog Usage

Some of the major C++ detector functions in tinycog are face, smile and saliency detection. There are also face and body features detections like nodding test ,face landmark test and finger count. 
[Guile](https://www.gnu.org/software/guile/guile.html) bindings are provided with the libdr_roboto.so library giving access to the C++ sensor functions within scheme. The need for Guile comes from using parts of the opencog engine for the robot's behavior. Ghost allows scripting dialog and behavior of artificial agents. It's syntax is made similar to ChatScript for a smooth transition. The Ghost module utilizes the OpenCog AtomSpace and the Attention Module for attention allocation and ghost rule selection. This means that a well functioning OpenCog needs to exist in your system. 

If you installed all the necessary dependancies like Guile (which actually get fulfilled when correctly installing opencog), let us elaborate some of the basic usages of guile. 

#### GUILE

Guile implements Scheme as described in the [Revised<sup>5</sup>](href="http://www.schemers.org/Documents/Standards/R5RS/) 
Report on the Algorithmic Language Scheme (usually known as R5RS), providing clean and general 
data and control structures. 

In its simplest form, Guile acts as an interactive interpreter for the Scheme programming language, 
reading and evaluating Scheme expressions the user enters from the terminal.

To start the shell you simply type `guile` on the terminal and a scheme prompt will appear. 
You can then start to execute scheme commands. To have a deep understanding on how to use guile by 
interacting with other languages and learn more advanced practical programming in scheme using 
guile you can refer to the [Guile manual](https://www.gnu.org/software/guile/manual/html_node/)

The most common thing we practice in guile while handling C++ functions is loading C-extensions. 
We can create a compiled code module of C functions. Once the module has been correctly installed, 
it should be possible to use it like this:
```
         (load-extension "./libSomeLibrary.so" "init_some_function")
```
 A compiled module should have a specially named module init function.  
 Guile knows about this special name and will call that function automatically after having linked in the library. 

In the above example libSomeLibrary.so is the module library name and 
“init_some_function” is the module initialization function.



### Usage

#### Materials required
* RaspberryPi 
* Portable speaker
* Pi Camera

Before using tinycog functionalities be sure to
1. Install [OpenCog](https://github.com/opencog/opencog) and its dependencies.
2. Install [TinyCog](https://github.com/opencog/TinyCog) and its dependencies.
3. Enable the camera via raspi-config

To test the c++ detector functions that currently have a scheme wrapper
1. cd to TinyCog/build and open a guile shell

We wrote a compiled code modules of the C++ functions.
In order to use and test those functionalities in your code you first have to load libdr_roboto, the module we  prepared  for the  C++ - Scheme binding.  In order to use it in guile we should load it by typing the following.

2. ```(load-extension "./libdr_roboto" "init_dr_roboto")```
 
note that only some of the c++ detector functions have a scheme wrapper in the libdr_roboto library. 

The init_dr_roboto function initialize the name of the scheme bindings for the C++ functions.
Those are det-face, det-face-smile,det-salient-point and act-say.

So once we load the library we can run the detector functions from guile. For example to run the face detection function we type ```(det-face)``` and It returns the size and positions of faces detected. 

Here are the descriptions of the functions you can use

```(det-face)```  ------------>To detect face.
It returns the size and positions of faces detected

```(det-face-smile)``` ------>To detect smile.
It returns the size and position of a face along with a true/false depending on if the face is smiling or not.

```(det-salient-point)``` ----->To detect a saliency.
It returns the point of saliency

```(act-say "your-input-text")``` ------->To make your speaker say the text.
It does TTS.
