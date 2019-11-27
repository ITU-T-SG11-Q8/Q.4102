// licensed under the GPL v2 as part of the git project http://git-scm.com/
/*
 * SHA1 routine optimized to do word accesses rather than byte accesses,
 * and to avoid unnecessary copies into the context array.
 *
 * This was initially based on the Mozilla SHA1 implementation, although
 * none of the original Mozilla code remains.
 */
#pragma once
#ifndef GIT_SHA1
#define GIT_SHA1

#define SHA1_DIGEST_BLOCKLEN 20

typedef struct {
    unsigned long long size;
    unsigned int H[5];
    unsigned int W[16];
} blk_SHA_CTX;

void blk_SHA1_Init(blk_SHA_CTX *ctx);
void blk_SHA1_Update(blk_SHA_CTX *ctx, const void *dataIn, unsigned long len);
void blk_SHA1_Final(unsigned char hashout[20], blk_SHA_CTX *ctx);

void SHA1_Encrypt(const unsigned char *pszMessage, unsigned int uPlainTextLen, unsigned char *pszDigest);
void SHA1_EncryptLR(const unsigned char *pszMessageL, const unsigned char *pszMessageR, unsigned char *pszDigest);
#endif

