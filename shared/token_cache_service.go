package jwt_token_cache

import (
	"strings"
)

var globalJwtTokenCache *JwtTokenCacheProvider

type TokenCacheItem struct {
	Name  string
	Token CachedJwtToken
}

type JwtTokenCacheProvider struct {
	Items []TokenCacheItem
}

func New() *JwtTokenCacheProvider {
	if globalJwtTokenCache != nil {
		return globalJwtTokenCache
	}

	globalJwtTokenCache = &JwtTokenCacheProvider{
		Items: make([]TokenCacheItem, 0),
	}

	return globalJwtTokenCache
}

func (c *JwtTokenCacheProvider) Get(name string) *CachedJwtToken {
	for _, item := range c.Items {
		if strings.EqualFold(name, item.Name) {
			return &item.Token
		}
	}

	return nil
}

func (c *JwtTokenCacheProvider) Set(name string, token CachedJwtToken) {
	found := false
	for _, item := range c.Items {
		if strings.EqualFold(name, item.Name) {
			found = true
			break
		}
	}

	if !found {
		c.Items = append(c.Items, TokenCacheItem{
			Name:  name,
			Token: token,
		})
	}
}
