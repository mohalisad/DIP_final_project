# DIP final project
## Group 7

### Method
1. Literature review
2. Problem definition; How to make stegano-image more resilient while transmitted on telegram.
3. Since telegram uses JPEG compression, implementing a JPEG steganography method that can provide robustness is in order
4. JPEG uses DCT to compress data so a steganography method based on DCT was implemented
5. In this implementation, we tried to combine the idea of the previous studies to improve security and stability
6. To maintain error correction, hamming encoding was implemented
7. The result shows that even if the image is subjected to some sort of distortion and degradation, we would be able to recover the message

#### Steganography
![baboon image](/samples/method_stegano.png)

<br>

#### Reverse Steganography
![baboon image](/samples/method_stegano_reverse.png)

### Images
#### Original Image
![baboon image](/samples/baboon.jpg)

#### Steganography Image 
![baboon image](/samples/stegano.jpg)

### Metrics
|               |      PSNR     |       MSE     |     SSIM      |
| ------------- | ------------- | ------------- | ------------- |
|          baboon       | 26.93  | 58.73  | 0.85  |
