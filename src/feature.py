# coding: utf-8

import cv2
import numpy as np


def harris_corner(img, k=0.04, block_size=2, kernel=11):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = np.float32(gray)/255

    corner_response = np.zeros(shape=gray.shape, dtype=np.float32)
    
    height, width, _ = img.shape
    dx = cv2.Sobel(gray, -1, 1, 0)
    dy = cv2.Sobel(gray, -1, 0, 1)
    Ixx = dx*dx
    Iyy = dy*dy
    Ixy = dx*dy
    
    cov_xx = cv2.boxFilter(Ixx, -1, (block_size, block_size), normalize=False)
    cov_yy = cv2.boxFilter(Iyy, -1, (block_size, block_size), normalize=False)
    cov_xy = cv2.boxFilter(Ixy, -1, (block_size, block_size), normalize=False)

    for y in range(height):
        for x in range(width):
            xx = cov_xx[y][x]
            yy = cov_yy[y][x]
            xy = cov_xy[y][x]

            det_M = xx*yy - xy**2
            trace_M = xx + yy
            
            R = det_M - k*trace_M**2
            corner_response[y][x] = R
            
    return corner_response
    

def extract_description(img, corner_response, threshold=0.01, kernel=3):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #gray = cv2.GaussianBlur(gray, (kernel, kernel), kernel)
    
    # Reduce corner
    features = np.zeros(shape=gray.shape, dtype=np.uint8)
    features[corner_response > threshold*corner_response.max()] = 255
    features[:10,:] = 0  # Trim feature on image edge
    features[-10:,:] = 0
    
    #plt.figure(figsize=(10,10))
    #plt.imshow(features, cmap='gray')
    #plt.colorbar()
    #plt.show()
    
    feature_positions = []
    feature_descriptions = np.zeros(shape=(1, kernel**2), dtype=np.float32)
    
    half_k = kernel//2
    height, width, _ = img.shape
    for y in range(half_k, height-half_k):
        for x in range(half_k, width-half_k):
            if features[y][x] == 255:
                feature_positions += [[y, x]]
                desc = corner_response[y-half_k:y+half_k+1, x-half_k:x+half_k+1]
                feature_descriptions = np.append(feature_descriptions, [desc.flatten()], axis=0)
                
    return feature_descriptions[1:], feature_positions

def matching(descriptor1, descriptor2, feature_position1, feature_position2):
    matched_pairs = []
    matched_pairs_rank = []
    
    for i in range(len(descriptor1)):
        distances = []
        y = feature_position1[i][0]
        for j in range(len(descriptor2)):
            diff = float('Inf')
            
            # only compare features that have similiar y-axis 
            if y-10 <= feature_position2[j][0] <= y+10:
                diff = descriptor1[i] - descriptor2[j]
                diff = (diff**2).sum()
            distances += [diff]
        
        sorted_index = np.argpartition(distances, 1)
        local_optimal = distances[sorted_index[0]]
        local_optimal2 = distances[sorted_index[1]]
        if local_optimal > local_optimal2:
            local_optimal, local_optimal2 = local_optimal2, local_optimal
        
        if local_optimal/local_optimal2 <= 0.5:
            paired_index = np.where(distances==local_optimal)[0][0]
            #print(featue_position1[i], paired_index)
            pair = [feature_position1[i], feature_position2[paired_index]]
            matched_pairs += [pair]
            matched_pairs_rank += [local_optimal]
            #print(pair)
    
    # Refine pairs
    sorted_rank_idx = np.argsort(matched_pairs_rank)
    sorted_match_pairs = np.asarray(matched_pairs)
    sorted_match_pairs = sorted_match_pairs[sorted_rank_idx]

    refined_matched_pairs = []
    for item in sorted_match_pairs:
        duplicated = False
        for refined_item in refined_matched_pairs:
            if refined_item[1] == list(item[1]):
                duplicated = True
                break
        if not duplicated:
            refined_matched_pairs += [item.tolist()]
            
    return refined_matched_pairs